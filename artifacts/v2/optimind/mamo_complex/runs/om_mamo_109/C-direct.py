import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    n = len(supply)
    regions = range(n)

    model = gp.Model("medical_supply_distribution")
    model.setParam("OutputFlag", 0)

    # x[i][j] = units shipped from region i to region j
    x = [[None] * n for _ in regions]
    for i in regions:
        for j in regions:
            if i != j:
                x[i][j] = model.addVar(lb=0.0, name=f"x_{i}_{j}")

    # Objective: minimize total transport cost
    obj = gp.LinExpr()
    for i in regions:
        for j in regions:
            if i != j:
                obj += transport_cost[i][j] * x[i][j]
    model.setObjective(obj, GRB.MINIMIZE)

    # Flow balance: supply[i] + inflow[i] - outflow[i] >= demand[i]
    for i in regions:
        inflow = gp.quicksum(x[j][i] for j in regions if j != i)
        outflow = gp.quicksum(x[i][j] for j in regions if j != i)
        model.addConstr(supply[i] + inflow - outflow >= demand[i], name=f"balance_{i}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}