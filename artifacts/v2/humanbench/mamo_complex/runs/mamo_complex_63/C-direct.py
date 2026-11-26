import gurobipy as gp
from gurobipy import GRB

def solve(params):
    stock = params["stock"]
    demand = params["demand"]
    transfer_cost = params["transfer_cost"]

    n = len(stock)
    hospitals = range(n)

    model = gp.Model("hospital_supply")
    model.setParam("OutputFlag", 0)

    # x[i][j] = units transferred from hospital i to hospital j
    x = [[None] * n for _ in hospitals]
    for i in hospitals:
        for j in hospitals:
            if i != j:
                x[i][j] = model.addVar(lb=0.0, name=f"x_{i}_{j}")

    # Objective: minimize total transfer cost
    obj = gp.LinExpr()
    for i in hospitals:
        for j in hospitals:
            if i != j:
                obj += transfer_cost[i][j] * x[i][j]
    model.setObjective(obj, GRB.MINIMIZE)

    # Flow balance: for each hospital, stock - outflow + inflow >= demand
    for i in hospitals:
        outflow = gp.quicksum(x[i][j] for j in hospitals if j != i)
        inflow = gp.quicksum(x[j][i] for j in hospitals if j != i)
        model.addConstr(stock[i] - outflow + inflow >= demand[i], name=f"balance_{i}")

    # Cannot send more than available stock net of what's needed
    # (non-negativity of remaining stock after outflow)
    for i in hospitals:
        outflow = gp.quicksum(x[i][j] for j in hospitals if j != i)
        model.addConstr(outflow <= stock[i], name=f"supply_cap_{i}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}