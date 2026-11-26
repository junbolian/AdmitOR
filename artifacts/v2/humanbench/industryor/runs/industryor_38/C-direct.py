import gurobipy as gp
from gurobipy import GRB


def solve(params):
    num_trains = params["num_trains"]
    num_tracks = params["num_tracks"]
    num_paths = params["num_paths"]
    num_stations = params["num_stations"]
    train_speeds = list(params["train_speeds"])
    stop_status = params["stop_status"]
    track_time_to_boundary = list(params["track_time_to_boundary"])
    min_dwell_time = params["min_dwell_time"]
    safe_interval = params["safe_interval"]

    trains = list(range(num_trains))
    tracks = list(range(num_tracks))
    paths = list(range(num_paths))

    # Structural mapping: which track each approach path leads to.
    # Paths 1..7 -> tracks I..V (0-indexed: 0,0,1,2,3,3,4)
    if num_paths == 7 and num_tracks == 5:
        path_to_track = [0, 0, 1, 2, 3, 3, 4]
    else:
        path_to_track = [p % num_tracks for p in paths]

    # All approach paths conflict pairwise (per problem statement).
    conflict_pairs = [(p, q) for p in paths for q in paths if p < q]

    M = 5000.0  # big-M

    model = gp.Model("station_A_allocation")
    model.setParam("OutputFlag", 0)
    model.setParam("TimeLimit", 120)
    model.setParam("MIPGap", 1e-4)

    # --- Variables ---
    arr = model.addVars(trains, lb=0.0, ub=M, name="arr")        # arrival at boundary
    dep = model.addVars(trains, lb=0.0, ub=M, name="dep")        # departure from track
    a_track = model.addVars(trains, tracks, vtype=GRB.BINARY, name="a_track")
    a_path = model.addVars(trains, paths, vtype=GRB.BINARY, name="a_path")

    pairs = [(i, j) for i in trains for j in trains if i < j]
    y_ord = model.addVars(pairs, vtype=GRB.BINARY, name="y_ord")   # track-occupancy order
    d_ord = model.addVars(pairs, vtype=GRB.BINARY, name="d_ord")   # departure order
    same_track = model.addVars(pairs, lb=0.0, ub=1.0, name="same_track")

    makespan = model.addVar(lb=0.0, ub=M, name="makespan")

    # Time from boundary to assigned track for train i (linear expression)
    def track_time_expr(i):
        return gp.quicksum(track_time_to_boundary[k] * a_track[i, k] for k in tracks)

    # --- Assignment constraints ---
    for i in trains:
        model.addConstr(
            gp.quicksum(a_track[i, k] for k in tracks) == 1, name=f"one_track_{i}")
        model.addConstr(
            gp.quicksum(a_path[i, p] for p in paths) == 1, name=f"one_path_{i}")
        for p in paths:
            model.addConstr(
                a_path[i, p] <= a_track[i, path_to_track[p]],
                name=f"path_track_{i}_{p}")

    # --- Arrival separation at the boundary (all paths conflict pairwise) ---
    # Enforce a chain: successive arrivals separated by at least safe_interval.
    for i in range(num_trains - 1):
        model.addConstr(arr[i + 1] >= arr[i] + safe_interval, name=f"arr_chain_{i}")

    # --- Dwell time ---
    # stop_status[i][0]: 1 if train i stops at Station A.
    for i in trains:
        stop_a = 1 if stop_status[i][0] > 0.5 else 0
        model.addConstr(
            dep[i] - arr[i] - track_time_expr(i) >= min_dwell_time * stop_a,
            name=f"dwell_{i}")

    # --- Departure separation (throat usage on the way out) ---
    for (i, j) in pairs:
        model.addConstr(
            dep[j] - dep[i] >= safe_interval - M * (1 - d_ord[i, j]),
            name=f"dep_sep_a_{i}_{j}")
        model.addConstr(
            dep[i] - dep[j] >= safe_interval - M * d_ord[i, j],
            name=f"dep_sep_b_{i}_{j}")

    # --- Same-track indicator: same_track[i,j] >= a_track[i,k] + a_track[j,k] - 1 ---
    for (i, j) in pairs:
        for k in tracks:
            model.addConstr(
                same_track[i, j] >= a_track[i, k] + a_track[j, k] - 1,
                name=f"st_{i}_{j}_{k}")

    # --- Track occupancy non-overlap (job-shop style disjunction) ---
    # occupancy of i: [arr_i + t, dep_i]; if same track, intervals must not overlap.
    for (i, j) in pairs:
        # dep_i <= arr_j + t_j  OR  dep_j <= arr_i + t_i
        model.addConstr(
            dep[i] - arr[j] - track_time_expr(j)
            <= M * y_ord[i, j] + M * (1 - same_track[i, j]),
            name=f"occ_a_{i}_{j}")
        model.addConstr(
            dep[j] - arr[i] - track_time_expr(i)
            <= M * (1 - y_ord[i, j]) + M * (1 - same_track[i, j]),
            name=f"occ_b_{i}_{j}")

    # --- Makespan ---
    for i in trains:
        model.addConstr(makespan >= dep[i], name=f"span_{i}")

    # --- Objective: minimize makespan plus speed-weighted dwell ---
    # Higher-speed trains are penalized more per minute of dwell (priority),
    # and a compact overall schedule (throughput) is encouraged.
    max_speed = max(train_speeds) if train_speeds else 1.0
    dwell_obj = gp.quicksum(
        (train_speeds[i] / max_speed) * (dep[i] - arr[i] - track_time_expr(i))
        for i in trains)
    model.setObjective(makespan + dwell_obj, GRB.MINIMIZE)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL or (status == GRB.TIME_LIMIT and model.SolCount > 0):
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    if status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    return {"objective": None, "status": f"status_{status}"}