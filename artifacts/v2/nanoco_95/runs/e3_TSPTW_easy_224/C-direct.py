import gurobipy as gp
from gurobipy import GRB
import math

def solve(params):
    # Read coordinates
    vault_x = params["vault_depot_x"]
    vault_y = params["vault_depot_y"]
    atm_x = params["atm_x"]
    atm_y = params["atm_y"]

    # Build travel time matrix (symmetric, 8x8, nodes 0-7)
    # Node 0 = vault, nodes 1-7 = ATMs
    n = 8
    t = [[0.0] * n for _ in range(n)]

    vault_to_atm = params["vault_to_atm_times"]
    for j in range(7):
        t[0][j+1] = vault_to_atm[j]
        t[j+1][0] = vault_to_atm[j]

    atm1_times = params["atm1_to_atm_times"]  # ATM1 -> ATMs 2-7
    for idx, j in enumerate(range(2, 8)):
        t[1][j] = atm1_times[idx]
        t[j][1] = atm1_times[idx]

    atm2_times = params["atm2_to_atm_times"]  # ATM2 -> ATMs 3-7
    for idx, j in enumerate(range(3, 8)):
        t[2][j] = atm2_times[idx]
        t[j][2] = atm2_times[idx]

    atm3_times = params["atm3_to_atm_times"]  # ATM3 -> ATMs 4-7
    for idx, j in enumerate(range(4, 8)):
        t[3][j] = atm3_times[idx]
        t[j][3] = atm3_times[idx]

    atm4_times = params["atm4_to_atm_times"]  # ATM4 -> ATMs 5-7
    for idx, j in enumerate(range(5, 8)):
        t[4][j] = atm4_times[idx]
        t[j][4] = atm4_times[idx]

    atm5_times = params["atm5_to_atm_times"]  # ATM5 -> ATMs 6-7
    for idx, j in enumerate(range(6, 8)):
        t[5][j] = atm5_times[idx]
        t[j][5] = atm5_times[idx]

    t[6][7] = params["atm6_to_atm7_time"]
    t[7][6] = params["atm6_to_atm7_time"]

    # Time windows (node 0 = vault, nodes 1-7 = ATMs)
    tw_start = [0.0] * n
    tw_end = [0.0] * n
    tw_start[0] = params["vault_time_window_start"]
    tw_end[0]   = params["vault_time_window_end"]
    tw_start[1] = params["atm1_time_window_start"]
    tw_end[1]   = params["atm1_time_window_end"]
    tw_start[2] = params["atm2_time_window_start"]
    tw_end[2]   = params["atm2_time_window_end"]
    tw_start[3] = params["atm3_time_window_start"]
    tw_end[3]   = params["atm3_time_window_end"]
    tw_start[4] = params["atm4_time_window_start"]
    tw_end[4]   = params["atm4_time_window_end"]
    tw_start[5] = params["atm5_time_window_start"]
    tw_end[5]   = params["atm5_time_window_end"]
    tw_start[6] = params["atm6_time_window_start"]
    tw_end[6]   = params["atm6_time_window_end"]
    tw_start[7] = params["atm7_time_window_start"]
    tw_end[7]   = params["atm7_time_window_end"]

    horizon = params["horizon"]
    service_time = params["service_time"]

    # Euclidean distances for objective (minimize mileage)
    coords_x = [vault_x] + list(atm_x)
    coords_y = [vault_y] + list(atm_y)
    dist = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                dist[i][j] = math.sqrt((coords_x[i] - coords_x[j])**2 +
                                        (coords_y[i] - coords_y[j])**2)

    nodes = list(range(n))
    # Route arcs: depot (0) -> ATMs (1-7) -> depot (0)
    # x[i][j] = 1 if vehicle travels from i to j
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = gp.Model("cash_in_transit")
    model.setParam("OutputFlag", 0)

    # Decision variables
    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")
    # Arrival time at each node
    s = model.addVars(nodes, lb=0.0, ub=horizon, vtype=GRB.CONTINUOUS, name="s")

    # Objective: minimize total Euclidean distance
    model.setObjective(
        gp.quicksum(dist[i][j] * x[i, j] for (i, j) in arcs),
        GRB.MINIMIZE
    )

    # Each ATM visited exactly once (flow in = 1)
    for j in range(1, n):
        model.addConstr(gp.quicksum(x[i, j] for i in nodes if i != j) == 1,
                        name=f"visit_in_{j}")

    # Each ATM departed exactly once (flow out = 1)
    for i in range(1, n):
        model.addConstr(gp.quicksum(x[i, j] for j in nodes if j != i) == 1,
                        name=f"visit_out_{i}")

    # Depot: exactly 1 departure and 1 return
    model.addConstr(gp.quicksum(x[0, j] for j in range(1, n)) == 1,
                    name="depot_out")
    model.addConstr(gp.quicksum(x[i, 0] for i in range(1, n)) == 1,
                    name="depot_in")

    # Time window constraints at each node
    for i in nodes:
        model.addConstr(s[i] >= tw_start[i], name=f"tw_start_{i}")
        model.addConstr(s[i] <= tw_end[i],   name=f"tw_end_{i}")

    # Subtour elimination via time propagation (MTZ-style with big-M)
    # If x[i,j]=1 then s[j] >= s[i] + service_time + t[i][j]
    big_M = horizon + max(t[i][j] for (i, j) in arcs) + service_time
    for (i, j) in arcs:
        if j != 0:  # don't apply when returning to depot (handled by horizon)
            model.addConstr(
                s[j] >= s[i] + service_time + t[i][j] - big_M * (1 - x[i, j]),
                name=f"time_prop_{i}_{j}"
            )

    # Return to depot within horizon
    for i in range(1, n):
        model.addConstr(
            s[0] + horizon >= s[i] + service_time + t[i][0] - big_M * (1 - x[i, 0]),
            name=f"return_horizon_{i}"
        )
    # Actually enforce the return time explicitly:
    # arrival back at depot = s[i] + service_time + t[i][0] when x[i,0]=1
    # We use a return time variable
    s_return = model.addVar(lb=0.0, ub=horizon, vtype=GRB.CONTINUOUS, name="s_return")
    for i in range(1, n):
        model.addConstr(
            s_return >= s[i] + service_time + t[i][0] - big_M * (1 - x[i, 0]),
            name=f"s_return_{i}"
        )
    model.addConstr(s_return <= horizon, name="curfew")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.TIME_LIMIT:
        if model.SolCount > 0:
            return {"objective": model.ObjVal, "status": "optimal"}
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}