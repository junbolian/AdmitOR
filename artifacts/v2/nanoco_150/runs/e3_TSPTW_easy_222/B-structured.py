# IR: {"sets":{"V":"range(num_nodes)","S":"V minus {0}","A":"{(i,j) in V x V: i != j}","D":"{0,1}"},"params":{"num_nodes":"params['num_nodes']","coords":"params['coords']; descriptive coordinates, not used to replace supplied distances","distance_matrix":"params['distance_matrix']","time_windows":"params['time_windows']","service_times":"params['service_times']","horizon":"params['horizon']","L[i]":"max(0,time_windows[i][0])","U[i]":"min(time_windows[i][1],horizon)","K":"num_nodes-1","M[i,j]":"max(0,U[i]+service_times[i]+distance_matrix[i][j]-L[j])"},"variables":{"x[i,j]":"binary for (i,j) in A","arrival[i]":"continuous in [L[i],U[i]] for i in V; arrival[0] is the initial hub time","hub_return":"continuous in [L[0],U[0]]","order[i]":"continuous in [1,K] for i in S"},"constraints":["sum(x[i,j] for j != i)=1 for i in V","sum(x[i,j] for i != j)=1 for j in V","arrival[j]>=arrival[i]+service_times[i]+distance_matrix[i][j]-M[i,j]*(1-x[i,j]) for (i,j) in A with j!=0","hub_return>=arrival[i]+service_times[i]+distance_matrix[i][0]-M[i,0]*(1-x[i,0]) for i in S","hub_return>=arrival[0]","order[i]-order[j]+K*x[i,j]<=K-1 for distinct i,j in S"],"objective":"minimize sum(distance_matrix[i][j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = int(params["num_nodes"])
    coords = params["coords"]
    distance_matrix = params["distance_matrix"]
    time_windows = params["time_windows"]
    service_times = params["service_times"]
    horizon = float(params["horizon"])

    if num_nodes < 2:
        raise ValueError("num_nodes must include a hub and at least one station.")

    nodes = range(num_nodes)
    stations = range(1, num_nodes)
    arcs = [(i, j) for i in nodes for j in nodes if i != j]
    station_count = num_nodes - 1

    lower = {
        i: max(0.0, float(time_windows[i][0]))
        for i in nodes
    }
    upper = {
        i: min(float(time_windows[i][1]), horizon)
        for i in nodes
    }

    if any(lower[i] > upper[i] for i in nodes):
        return {"objective": None, "status": "infeasible"}

    model = pyo.ConcreteModel()

    model.node_set = pyo.Set(initialize=nodes, ordered=True)
    model.station_set = pyo.Set(initialize=stations, ordered=True)
    model.arc_set = pyo.Set(dimen=2, initialize=arcs)
    model.coordinate_dimensions = pyo.Set(initialize=[0, 1])

    # The supplied distance matrix is authoritative; coordinates are metadata.
    model.coordinates = pyo.Param(
        model.node_set,
        model.coordinate_dimensions,
        initialize={(i, axis): coords[i][axis] for i in nodes for axis in (0, 1)},
        within=pyo.Reals,
    )
    model.travel_distance = pyo.Param(
        model.arc_set,
        initialize={(i, j): distance_matrix[i][j] for i, j in arcs},
        within=pyo.NonNegativeReals,
    )
    model.service_duration = pyo.Param(
        model.node_set,
        initialize={i: service_times[i] for i in nodes},
        within=pyo.NonNegativeReals,
    )
    model.time_lower = pyo.Param(model.node_set, initialize=lower)
    model.time_upper = pyo.Param(model.node_set, initialize=upper)

    model.big_m = pyo.Param(
        model.arc_set,
        initialize={
            (i, j): max(
                0.0,
                upper[i]
                + float(service_times[i])
                + float(distance_matrix[i][j])
                - lower[j],
            )
            for i, j in arcs
        },
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(model.arc_set, domain=pyo.Binary)
    model.arrival = pyo.Var(
        model.node_set,
        domain=pyo.Reals,
        bounds=lambda mdl, i: (lower[i], upper[i]),
    )
    model.hub_return = pyo.Var(
        domain=pyo.Reals,
        bounds=(lower[0], upper[0]),
    )
    model.visit_order = pyo.Var(
        model.station_set,
        domain=pyo.Reals,
        bounds=(1, station_count),
    )

    def outgoing_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.node_set if j != i) == 1

    model.one_departure = pyo.Constraint(model.node_set, rule=outgoing_rule)

    def incoming_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.node_set if i != j) == 1

    model.one_arrival = pyo.Constraint(model.node_set, rule=incoming_rule)

    def timing_rule(mdl, i, j):
        destination_time = mdl.hub_return if j == 0 else mdl.arrival[j]
        return destination_time >= (
            mdl.arrival[i]
            + mdl.service_duration[i]
            + mdl.travel_distance[i, j]
            - mdl.big_m[i, j] * (1 - mdl.x[i, j])
        )

    # Inequalities allow waiting before delivery to satisfy early time limits.
    # Separate initial and return hub times avoid a cyclic time contradiction.
    model.route_timing = pyo.Constraint(model.arc_set, rule=timing_rule)
    model.return_after_start = pyo.Constraint(
        expr=model.hub_return >= model.arrival[0]
    )

    def subtour_rule(mdl, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            mdl.visit_order[i]
            - mdl.visit_order[j]
            + station_count * mdl.x[i, j]
            <= station_count - 1
        )

    model.subtour_elimination = pyo.Constraint(
        model.station_set,
        model.station_set,
        rule=subtour_rule,
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.travel_distance[i, j] * model.x[i, j]
            for i, j in model.arc_set
        ),
        sense=pyo.minimize,
    )

    # APPsi can raise RuntimeError when it cannot load a feasible solution.
    # Objective retrieval below is the sole test for successful completion.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}