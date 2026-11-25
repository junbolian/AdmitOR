import gurobipy as gp
from gurobipy import GRB
import math

def solve(params):
    vault_x = params["vault_x"]
    vault_y = params["vault_y"]
    atm_x = params["atm_x"]
    atm_y = params["atm_y"]
    travel_time_0_to_atm = params["travel_time_0_to_atm"]
    travel_time_atm1_to_atm = params["travel_time_atm1_to_atm"]
    travel_time_atm2_to_atm = params["travel_time_atm2_to_atm"]
    travel_time_atm3_to_atm = params["travel_time_atm3_to_atm"]
    travel_time_atm4_to_atm = params["travel_time_atm4_to_atm"]
    travel_time_atm5_to_atm = params["travel_time_atm5_to_atm"]
    travel_time_atm6_to_atm7 = params["travel_time_atm6_to_atm7"]
    vault_window_start = params["vault_window_start"]
    vault_window_end = params["vault_window_end"]
    atm_window_start = params["atm_window_start"]
    atm_window_end = params["atm_window_end"]
    horizon = params["horizon"]

    n = 8
    nodes = list(range(n))
    atm_nodes = list(range(1, n))

    coords_x = [vault_x] + list(atm_x)
    coords_y = [vault_y] + list(atm_y)

    # Euclidean distance matrix for objective
    dist = {}
    for i in nodes:
        for j in nodes:
            dist[i, j] = 0.0 if i == j else math.sqrt(
                (coords_x[i] - coords_x[j])**2 + (coords_y[i] - coords_y[j])**2
            )

    # Travel time matrix (symmetric)
    tt = [[0.0] * n for _ in range(n)]

    for idx, val in enumerate(travel_time_0_to_atm):
        j = idx + 1
        tt[0][j] = val
        tt[j][0] = val

    for idx, val in enumerate(travel_time_atm1_to_atm):
        j = idx + 2
        tt[1][j] = val
        tt[j][1] = val

    for idx, val in enumerate(travel_time_atm2_to_atm):
        j = idx + 3
        tt[2][j] = val
        tt[j][2] = val

    for idx, val in enumerate(travel_time_atm3_to_atm):
        j = idx + 4
        tt[3][j] = val
        tt[j][3] = val

    for idx, val in enumerate(travel_time_atm4_to_atm):
        j = idx + 5
        tt[4][j] = val
        tt[j][4] = val

    for idx, val in enumerate(travel_time_atm5_to_atm):
        j = idx + 6
        tt[5][j] = val
        tt[j][5] = val

    tt[6][7] = travel_time_atm6_to_atm7
    tt[7][6] = travel_time_atm6_to_atm7

    # Time windows for ATMs only (indices 1-7 → list index 0-6)
    tw_start = list(atm_window_start)
    tw_end = list(atm_window_end)

    model = gp.Model("cash_transit_vrptw")
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if vehicle travels from node i to node j
    x = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # t[i] = service/arrival time at ATM node i (1-indexed in atm_nodes)
    # Bounds enforce time windows for ATMs
    t = {}
    for i in atm_nodes:
        t[i] = model.addVar(
            lb=tw_start[i - 1],
            ub=tw_end[i - 1],
            vtype=GRB.CONTINUOUS,
            name=f"t_{i}"
        )

    # t_return: arrival time back at vault — must be within vault window and <= horizon
    t_return = model.addVar(
        lb=vault_window_start,
        ub=min(vault_window_end, horizon),
        vtype=GRB.CONTINUOUS,
        name="t_return"
    )

    model.update()

    # Objective: minimize total Euclidean distance
    model.setObjective(
        gp.quicksum(dist[i, j] * x[i, j] for i in nodes for j in nodes if i != j),
        GRB.MINIMIZE
    )

    # Depart vault exactly once
    model.addConstr(
        gp.quicksum(x[0, j] for j in atm_nodes) == 1,
        name="depart_vault"
    )

    # Return to vault exactly once
    model.addConstr(
        gp.quicksum(x[i, 0] for i in atm_nodes) == 1,
        name="return_vault"
    )

    # Each ATM entered exactly once
    for j in atm_nodes:
        model.addConstr(
            gp.quicksum(x[i, j] for i in nodes if i != j) == 1,
            name=f"enter_{j}"
        )

    # Each ATM exited exactly once
    for i in atm_nodes:
        model.addConstr(
            gp.quicksum(x[i, j] for j in nodes if j != i) == 1,
            name=f"exit_{i}"
        )

    # Big-M for time propagation and subtour elimination
    big_M = horizon + max(tt[i][j] for i in nodes for j in nodes if i != j)

    # Departure from vault at time 0: if x[0,j]=1 then t[j] >= tt[0][j]
    for j in atm_nodes:
        model.addConstr(
            t[j] >= tt[0][j] - big_M * (1 - x[0, j]),
            name=f"depart_vault_time_{j}"
        )

    # Propagation between ATM nodes: if x[i,j]=1 then t[j] >= t[i] + tt[i][j]
    for i in atm_nodes:
        for j in atm_nodes:
            if i != j:
                model.addConstr(
                    t[j] >= t[i] + tt[i][j] - big_M * (1 - x[i, j]),
                    name=f"time_prop_{i}_{j}"
                )

    # Return to vault: if x[i,0]=1 then t_return >= t[i] + tt[i][0]
    for i in atm_nodes:
        model.addConstr(
            t_return >= t[i] + tt[i][0] - big_M * (1 - x[i, 0]),
            name=f"return_time_{i}"
        )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}