import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]  # dict or list indexed by hospital
    demand = params["demand"]  # dict or list indexed by hospital
    cost = params["cost"]      # cost[i][j]: transfer cost from i to j

    # Normalize to list-based indexing
    hospitals = list(range(len(supply)))
    s = [supply[i] for i in hospitals]
    d = [demand[i] for i in hospitals]
    c = [[cost[i][j] for j in hospitals] for i in hospitals]

    model = gp.Model("hospital_supply_transfer")
    model.setParam("OutputFlag", 0)

    # x[i][j] = units transferred from hospital i to hospital j
    x = [[None] * len(hospitals) for _ in hospitals]
    for i in hospitals:
        for j in hospitals:
            if i != j:
                x[i][j] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"x_{i}_{j}")

    # Objective: minimize total transfer cost
    obj = gp.LinExpr()
    for i in hospitals:
        for j in hospitals:
            if i != j:
                obj += c[i][j] * x[i][j]
    model.setObjective(obj, GRB.MINIMIZE)

    # Flow balance: for each hospital, supply + inflow - outflow >= demand
    for i in hospitals:
        inflow = gp.LinExpr()
        outflow = gp.LinExpr()
        for j in hospitals:
            if j != i:
                inflow += x[j][i]
                outflow += x[i][j]
        # Net supply after transfers must meet demand
        # s[i] + inflow - outflow >= d[i]
        model.addConstr(s[i] + inflow - outflow >= d[i], name=f"demand_{i}")
        # Cannot send out more than available (after receiving)
        # Equivalently: outflow <= s[i] + inflow
        model.addConstr(outflow <= s[i] + inflow, name=f"supply_{i}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}