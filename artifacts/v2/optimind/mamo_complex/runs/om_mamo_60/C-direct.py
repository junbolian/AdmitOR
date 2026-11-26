import gurobipy as gp
from gurobipy import GRB

def solve(params):
    stock = params["stock"]
    demand = params["demand"]

    regions = [1, 2, 3, 4, 5, 6]

    cost = {}
    for i in regions:
        for j in regions:
            if i != j:
                key = f"cost_{i}_{j}"
                cost[(i, j)] = params[key]

    model = gp.Model("resource_distribution")
    model.setParam("OutputFlag", 0)

    flow = {}
    for i in regions:
        for j in regions:
            if i != j:
                flow[(i, j)] = model.addVar(lb=0.0, name=f"flow_{i}_{j}")

    model.setObjective(
        gp.quicksum(cost[(i, j)] * flow[(i, j)] for i in regions for j in regions if i != j),
        GRB.MINIMIZE
    )

    for i in regions:
        outflow = gp.quicksum(flow[(i, j)] for j in regions if j != i)
        inflow = gp.quicksum(flow[(j, i)] for j in regions if j != i)
        model.addConstr(outflow - inflow == stock[i - 1] - demand[i - 1], name=f"balance_{i}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}