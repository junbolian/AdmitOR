import gurobipy as gp
from gurobipy import GRB


def solve(params):
    profit = params["profit_per_unit"]      # list of 3
    hold_cost = params["holding_cost"]      # scalar
    g_cap_val = params["grinder_capacity"]  # scalar
    d_cap_val = params["drill_capacity"]    # scalar (normal periods)
    b_cap_val = params["borer_capacity"]    # scalar (normal periods)
    g_time = params["grinder_time"]         # list of 3
    d_time = params["drill_time"]           # list of 3
    b_time = params["borer_time"]           # list of 3
    inv_cap = params["max_inventory"]       # scalar
    max_sales = params["max_sales"]         # 4 x 3
    fin_inv = params["final_inventory"]     # list of 3

    T = range(4)
    P = range(3)

    # Build per-period capacity arrays using problem structure:
    # drill unavailable (0) in period 0, borer unavailable (0) in period 1
    g_cap = [g_cap_val, g_cap_val, g_cap_val, g_cap_val]
    d_cap = [0, d_cap_val, d_cap_val, d_cap_val]
    b_cap = [b_cap_val, 0, b_cap_val, b_cap_val]

    model = gp.Model("factory")
    model.Params.OutputFlag = 0

    make = model.addVars(T, P, lb=0.0, vtype=GRB.CONTINUOUS, name="make")
    store = model.addVars(T, P, lb=0.0, ub=inv_cap, vtype=GRB.CONTINUOUS, name="store")
    sell = model.addVars(T, P, lb=0.0, vtype=GRB.CONTINUOUS, name="sell")

    # Sales upper bounds
    for t in T:
        for p in P:
            sell[t, p].ub = max_sales[t][p]

    # Inventory balance constraints
    for t in T:
        for p in P:
            if t == 0:
                model.addConstr(make[t, p] == sell[t, p] + store[t, p],
                                name=f"balance_{t}_{p}")
            else:
                model.addConstr(store[t - 1, p] + make[t, p] == sell[t, p] + store[t, p],
                                name=f"balance_{t}_{p}")

    # Machine capacity constraints
    for t in T:
        model.addConstr(
            gp.quicksum(g_time[p] * make[t, p] for p in P) <= g_cap[t],
            name=f"grinder_{t}"
        )
        model.addConstr(
            gp.quicksum(d_time[p] * make[t, p] for p in P) <= d_cap[t],
            name=f"drill_{t}"
        )
        model.addConstr(
            gp.quicksum(b_time[p] * make[t, p] for p in P) <= b_cap[t],
            name=f"borer_{t}"
        )

    # Final inventory requirements
    for p in P:
        model.addConstr(store[3, p] == fin_inv[p], name=f"final_inv_{p}")

    # Objective: total revenue minus holding costs
    revenue = gp.quicksum(profit[p] * sell[t, p] for t in T for p in P)
    holding = gp.quicksum(hold_cost * store[t, p] for t in T for p in P)
    model.setObjective(revenue - holding, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    if model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": f"failed: status {model.Status}"}