import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Read all parameters from the params dict
    vault_x = params["vault_x"]
    vault_y = params["vault_y"]
    atm_x = params["atm_x"]
    atm_y = params["atm_y"]

    tt0 = params["travel_time_0_to_atm"]       # to ATMs 1-7 (7 values)
    tt1 = params["travel_time_atm1_to_atm"]    # to ATMs 2-7 (6 values)
    tt2 = params["travel_time_atm2_to_atm"]    # to ATMs 3-7 (5 values)
    tt3 = params["travel_time_atm3_to_atm"]     # to ATMs 4-7 (4 values)
    tt4 = params["travel_time_atm4_to_atm"]     # to ATMs 5-7 (3 values)
    tt5 = params["travel_time_atm5_to_atm"]     # to ATMs 6-7 (2 values)
    tt6 = params["travel_time_atm6_to_atm7"]    # to ATM 7   (1 value)

    vault_window_start = params["vault_window_start"]
    vault_window_end = params["vault_window_end"]
    atm_window_start = params["atm_window_start"]   # 7 values
    atm_window_end = params["atm_window_end"]        # 7 values
    horizon = params["horizon"]

    # ------------------------------------------------------------------
    # Build symmetric distance matrix for original 8 nodes (0 = vault, 1-7 = ATMs)
    # ------------------------------------------------------------------
    N = 8
    d = [[0.0] * N for _ in range(N)]

    # Vault (0) to ATMs 1-7
    for j in range(1, 8):
        d[0][j] = tt0[j - 1]
        d[j][0] = tt0[j - 1]
    # ATM 1 to ATMs 2-7
    for j in range(2, 8):
        d[1][j] = tt1[j - 2]
        d[j][1] = tt1[j - 2]
    # ATM 2 to ATMs 3-7
    for j in range(3, 8):
        d[2][j] = tt2[j - 3]
        d[j][2] = tt2[j - 3]
    # ATM 3 to ATMs 4-7
    for j in range(4, 8):
        d[3][j] = tt3[j - 4]
        d[j][3] = tt3[j - 4]
    # ATM 4 to ATMs 5-7
    for j in range(5, 8):
        d[4][j] = tt4[j - 5]
        d[j][4] = tt4[j - 5]
    # ATM 5 to ATMs 6-7
    for j in range(6, 8):
        d[5][j] = tt5[j - 6]
        d[j][5] = tt5[j - 6]
    # ATM 6 to ATM 7
    d[6][7] = tt6
    d[7][6] = tt6

    # ------------------------------------------------------------------
    # Time windows for nodes 0-7
    # ------------------------------------------------------------------
    e = [0.0] * N
    l = [0.0] * N
    e[0] = float(vault_window_start)
    l[0] = float(vault_window_end)
    for i in range(1, 8):
        e[i] = float(atm_window_start[i - 1])
        l[i] = float(atm_window_end[i - 1])

    # ------------------------------------------------------------------
    # Extended network: node 8 is a dummy end-depot (copy of vault).
    # The vehicle starts at node 0, visits ATMs 1-7, and terminates at node 8.
    # ------------------------------------------------------------------
    NN = 9
    d_ext = [[0.0] * NN for _ in range(NN)]
    for i in range(N):
        for j in range(N):
            d_ext[i][j] = d[i][j]
    # Distance from each ATM to the end-depot = distance from that ATM to vault
    for i in range(1, 8):
        d_ext[i][8] = d[i][0]

    e_ext = list(e) + [float(vault_window_start)]
    l_ext = list(l) + [float(min(vault_window_end, horizon))]

    # Valid arcs: start(0) -> ATMs, ATM -> ATM, ATM -> end(8)
    # No arcs into 0, no arcs from 8, no direct 0->8
    arcs = []
    for i in range(NN):
        for j in range(NN):
            if i == j:
                continue
            if j == 0:
                continue
            if i == 8:
                continue
            if i == 0 and j == 8:
                continue
            arcs.append((i, j))

    # Big-M for time-propagation linearisation
    max_d = max(d_ext[i][j] for i in range(NN) for j in range(NN))
    M = 2.0 * float(horizon) + max_d

    # ------------------------------------------------------------------
    # Model
    # ------------------------------------------------------------------
    model = gp.Model("tsptw")
    model.Params.OutputFlag = 0

    x = {}
    for (i, j) in arcs:
        x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    t = {}
    for i in range(NN):
        t[i] = model.addVar(
            lb=e_ext[i], ub=l_ext[i], vtype=GRB.CONTINUOUS, name=f"t_{i}"
        )

    # Objective: minimise total travel time
    model.setObjective(
        gp.quicksum(d_ext[i][j] * x[i, j] for (i, j) in arcs),
        GRB.MINIMIZE,
    )

    # ------------------------------------------------------------------
    # Degree constraints
    # ------------------------------------------------------------------
    # Start depot (0): exactly one outgoing arc
    model.addConstr(
        gp.quicksum(x[0, j] for j in range(1, 8)) == 1,
        name="out_depot",
    )
    # End depot (8): exactly one incoming arc
    model.addConstr(
        gp.quicksum(x[i, 8] for i in range(1, 8)) == 1,
        name="in_depot",
    )
    # Each ATM (1-7): in-degree = 1 and out-degree = 1
    for k in range(1, 8):
        model.addConstr(
            gp.quicksum(x[a, b] for (a, b) in arcs if b == k) == 1,
            name=f"in_{k}",
        )
        model.addConstr(
            gp.quicksum(x[a, b] for (a, b) in arcs if a == k) == 1,
            name=f"out_{k}",
        )

    # ------------------------------------------------------------------
    # Time propagation (also acts as subtour elimination)
    # ------------------------------------------------------------------
    for (i, j) in arcs:
        model.addConstr(
            t[j] >= t[i] + d_ext[i][j] - M * (1 - x[i, j]),
            name=f"time_{i}_{j}",
        )

    # Return-to-vault must respect the operational horizon
    model.addConstr(t[8] <= float(horizon), name="horizon_limit")

    # ------------------------------------------------------------------
    # Solve
    # ------------------------------------------------------------------
    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.status}"}