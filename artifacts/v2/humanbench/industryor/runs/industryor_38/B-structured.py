# IR: {"sets":{"T":"range(num_trains)","K":"range(num_tracks)","P":"range(num_paths)","S":"range(num_stations)","Q":"{(i,j):i,j in T,i<j}"},"params":["num_trains","num_tracks","num_paths","num_stations","train_speeds[T]","stop_status[T,S]","track_time_to_boundary[K]","min_dwell_time","safe_interval"],"structure":{"path_track":[0,0,1,2,3,3,4],"all_paths_conflict":true,"representative_paths":[0,2,3,4,6]},"derived":{"d[i]":"min_dwell_time*stop_status[i,0]","b_min":"min(track_time_to_boundary)","H":"sum_i d[i]+num_trains*b_min+(num_trains-1)*safe_interval","M":"H+safe_interval"},"variables":{"track_choice[T,K]":"binary","path_choice[T,P]":"binary","before[Q]":"binary","preparation_start[T]":"continuous [0,H]","departure[T]":"continuous [0,H]","clearance[T]":"continuous [0,H]","makespan":"continuous [0,H]"},"constraints":["sum_k track_choice[i,k]=1","sum_p path_choice[i,p]=1","track_choice[i,k]=sum_{p:path_track[p]=k} path_choice[i,p]","path_choice[i,p]=0 for nonrepresentative p","before[i,j]=1 for (i,j) in Q with d[i]=d[j]","departure[i]>=preparation_start[i]+d[i]","clearance[i]=departure[i]+sum_k track_time_to_boundary[k]*track_choice[i,k]","departure[j]>=clearance[i]+safe_interval-M*(1-before[i,j]) for (i,j) in Q","departure[i]>=clearance[j]+safe_interval-M*before[i,j] for (i,j) in Q","preparation_start[j]>=clearance[i]+safe_interval-M*(3-before[i,j]-track_choice[i,k]-track_choice[j,k]) for (i,j) in Q,k in K","preparation_start[i]>=clearance[j]+safe_interval-M*(2+before[i,j]-track_choice[i,k]-track_choice[j,k]) for (i,j) in Q,k in K","makespan>=clearance[i]","makespan>=min_i d[i]+sum_{i,k} track_time_to_boundary[k]*track_choice[i,k]+(num_trains-1)*safe_interval"],"objective":"minimize makespan"}
#
# Assumptions:
# - Minimize the time when all trains have cleared Station A.
# - All trains are available at relative time zero.
# - A station track is occupied from preparation start through clearance.
# - Every departure path conflicts with every other departure path.
# - The safe interval separates consecutive uses of a conflicting resource.
# - Boundary times are supplied directly; no speed adjustment is inferred.
# - Speeds and downstream stop flags are retained as data. An A-G timetable
#   cannot be inferred without interstation distances or running times.
# - Inputs are zero-based sequences in the order specified in the question.
# - The required return interface exposes only objective and status.
#
# Performance corrections:
# - Trains with identical dwell requirements are interchangeable in this
#   Station A model. Fix their relative order to remove factorial symmetry.
# - Paths serving the same track are interchangeable because all paths
#   conflict. Retain one representative per track.
# - Add a workload lower bound on makespan.
# - Use a serial schedule on a fastest track to bound the planning horizon.

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_trains = params["num_trains"]
    num_tracks = params["num_tracks"]
    num_paths = params["num_paths"]
    num_stations = params["num_stations"]
    train_speeds = params["train_speeds"]
    stop_status = params["stop_status"]
    track_time_to_boundary = params["track_time_to_boundary"]
    min_dwell_time = params["min_dwell_time"]
    safe_interval = params["safe_interval"]

    sizes = (num_trains, num_tracks, num_paths, num_stations)
    if any(
        isinstance(size, bool) or not isinstance(size, int) or size <= 0
        for size in sizes
    ):
        return {"objective": None, "status": "invalid_dimensions"}

    # Structural topology from the problem statement.
    path_track = (0, 0, 1, 2, 3, 3, 4)
    if (
        num_tracks != len(set(path_track))
        or num_paths != len(path_track)
        or num_stations != 7
    ):
        return {"objective": None, "status": "unsupported_topology"}

    if (
        len(train_speeds) != num_trains
        or len(stop_status) != num_trains
        or len(track_time_to_boundary) != num_tracks
        or any(len(row) != num_stations for row in stop_status)
    ):
        return {"objective": None, "status": "invalid_data_shape"}

    try:
        speeds = [float(value) for value in train_speeds]
        boundary_times = [float(value) for value in track_time_to_boundary]
        stops = [[float(value) for value in row] for row in stop_status]
        dwell_minimum = float(min_dwell_time)
        separation = float(safe_interval)
    except (TypeError, ValueError, OverflowError):
        return {"objective": None, "status": "invalid_numeric_data"}

    if any(not math.isfinite(value) or value <= 0 for value in speeds):
        return {"objective": None, "status": "invalid_train_speeds"}

    if any(
        not math.isfinite(value) or value < 0
        for value in boundary_times + [dwell_minimum, separation]
    ):
        return {"objective": None, "status": "invalid_time_data"}

    if any(value not in (0, 1) for row in stops for value in row):
        return {"objective": None, "status": "invalid_stop_status"}

    train_ids = range(num_trains)
    track_ids = range(num_tracks)
    path_ids = range(num_paths)
    station_ids = range(num_stations)

    train_pairs = [
        (first, second)
        for first in train_ids
        for second in range(first + 1, num_trains)
    ]
    dwell_times = [
        dwell_minimum * stops[train_id][0] for train_id in train_ids
    ]
    representative_paths = {
        next(
            path_id
            for path_id in path_ids
            if path_track[path_id] == track_id
        )
        for track_id in track_ids
    }

    fastest_boundary_time = min(boundary_times)
    horizon = (
        sum(dwell_times)
        + num_trains * fastest_boundary_time
        + (num_trains - 1) * separation
    )
    big_m = horizon + separation

    if not math.isfinite(horizon) or not math.isfinite(big_m):
        return {"objective": None, "status": "invalid_time_scale"}

    model = pyo.ConcreteModel()

    model.trains = pyo.Set(initialize=train_ids, ordered=True)
    model.tracks = pyo.Set(initialize=track_ids, ordered=True)
    model.paths = pyo.Set(initialize=path_ids, ordered=True)
    model.stations = pyo.Set(initialize=station_ids, ordered=True)
    model.train_pairs = pyo.Set(
        dimen=2, initialize=train_pairs, ordered=True
    )

    model.speed_data = pyo.Param(
        model.trains,
        initialize={
            train_id: speeds[train_id] for train_id in train_ids
        },
        within=pyo.PositiveReals,
    )
    model.stop_data = pyo.Param(
        model.trains,
        model.stations,
        initialize={
            (train_id, station_id): stops[train_id][station_id]
            for train_id in train_ids
            for station_id in station_ids
        },
        within=pyo.Binary,
    )
    model.boundary_time = pyo.Param(
        model.tracks,
        initialize={
            track_id: boundary_times[track_id] for track_id in track_ids
        },
        within=pyo.NonNegativeReals,
    )
    model.minimum_dwell = pyo.Param(
        initialize=dwell_minimum, within=pyo.NonNegativeReals
    )
    model.separation_time = pyo.Param(
        initialize=separation, within=pyo.NonNegativeReals
    )
    model.horizon_limit = pyo.Param(
        initialize=horizon, within=pyo.NonNegativeReals
    )
    model.disjunction_bound = pyo.Param(
        initialize=big_m, within=pyo.NonNegativeReals
    )

    model.track_choice = pyo.Var(
        model.trains, model.tracks, domain=pyo.Binary
    )
    model.path_choice = pyo.Var(
        model.trains, model.paths, domain=pyo.Binary
    )
    model.before = pyo.Var(model.train_pairs, domain=pyo.Binary)
    model.preparation_start = pyo.Var(
        model.trains, domain=pyo.NonNegativeReals, bounds=(0, horizon)
    )
    model.departure = pyo.Var(
        model.trains, domain=pyo.NonNegativeReals, bounds=(0, horizon)
    )
    model.clearance = pyo.Var(
        model.trains, domain=pyo.NonNegativeReals, bounds=(0, horizon)
    )
    model.makespan = pyo.Var(
        domain=pyo.NonNegativeReals, bounds=(0, horizon)
    )

    # Fixed variables implement the symmetry constraints in the IR.
    for train_id in train_ids:
        for path_id in path_ids:
            if path_id not in representative_paths:
                model.path_choice[train_id, path_id].fix(0)

    # All other train-specific inputs are inactive in the Station A
    # scheduling constraints, so equal-dwell trains can be relabeled.
    for first, second in train_pairs:
        if dwell_times[first] == dwell_times[second]:
            model.before[first, second].fix(1)

    model.one_track = pyo.Constraint(
        model.trains,
        rule=lambda mdl, train_id: sum(
            mdl.track_choice[train_id, track_id]
            for track_id in mdl.tracks
        ) == 1,
    )
    model.one_path = pyo.Constraint(
        model.trains,
        rule=lambda mdl, train_id: sum(
            mdl.path_choice[train_id, path_id]
            for path_id in mdl.paths
        ) == 1,
    )
    model.path_track_link = pyo.Constraint(
        model.trains,
        model.tracks,
        rule=lambda mdl, train_id, track_id: (
            mdl.track_choice[train_id, track_id]
            == sum(
                mdl.path_choice[train_id, path_id]
                for path_id in mdl.paths
                if path_track[path_id] == track_id
            )
        ),
    )
    model.dwell_requirement = pyo.Constraint(
        model.trains,
        rule=lambda mdl, train_id: (
            mdl.departure[train_id]
            >= mdl.preparation_start[train_id]
            + mdl.minimum_dwell * mdl.stop_data[train_id, 0]
        ),
    )
    model.clearance_definition = pyo.Constraint(
        model.trains,
        rule=lambda mdl, train_id: (
            mdl.clearance[train_id]
            == mdl.departure[train_id]
            + sum(
                mdl.boundary_time[track_id]
                * mdl.track_choice[train_id, track_id]
                for track_id in mdl.tracks
            )
        ),
    )
    model.throat_forward = pyo.Constraint(
        model.train_pairs,
        rule=lambda mdl, first, second: (
            mdl.departure[second]
            >= mdl.clearance[first]
            + mdl.separation_time
            - mdl.disjunction_bound * (1 - mdl.before[first, second])
        ),
    )
    model.throat_reverse = pyo.Constraint(
        model.train_pairs,
        rule=lambda mdl, first, second: (
            mdl.departure[first]
            >= mdl.clearance[second]
            + mdl.separation_time
            - mdl.disjunction_bound * mdl.before[first, second]
        ),
    )
    model.track_forward = pyo.Constraint(
        model.train_pairs,
        model.tracks,
        rule=lambda mdl, first, second, track_id: (
            mdl.preparation_start[second]
            >= mdl.clearance[first]
            + mdl.separation_time
            - mdl.disjunction_bound
            * (
                3
                - mdl.before[first, second]
                - mdl.track_choice[first, track_id]
                - mdl.track_choice[second, track_id]
            )
        ),
    )
    model.track_reverse = pyo.Constraint(
        model.train_pairs,
        model.tracks,
        rule=lambda mdl, first, second, track_id: (
            mdl.preparation_start[first]
            >= mdl.clearance[second]
            + mdl.separation_time
            - mdl.disjunction_bound
            * (
                2
                + mdl.before[first, second]
                - mdl.track_choice[first, track_id]
                - mdl.track_choice[second, track_id]
            )
        ),
    )
    model.makespan_bound = pyo.Constraint(
        model.trains,
        rule=lambda mdl, train_id: (
            mdl.makespan >= mdl.clearance[train_id]
        ),
    )

    # The shared throat must process every boundary traversal, with
    # separation between consecutive traversals. The earliest possible
    # first departure is bounded below by the minimum dwell requirement.
    model.throat_workload_bound = pyo.Constraint(
        expr=(
            model.makespan
            >= min(dwell_times)
            + sum(
                model.boundary_time[track_id]
                * model.track_choice[train_id, track_id]
                for train_id in model.trains
                for track_id in model.tracks
            )
            + (num_trains - 1) * model.separation_time
        )
    )

    model.total_clearance_time = pyo.Objective(
        expr=model.makespan, sense=pyo.minimize
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPSI raises this when it cannot load a feasible solution.
        # Propagate unrelated runtime errors.
        if "feasible solution" not in str(exc).lower():
            raise

    # Success is determined only by retrieving the objective value.
    try:
        obj_val = float(pyo.value(model.total_clearance_time))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}