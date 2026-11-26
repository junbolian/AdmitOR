import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = {}
    regions = [1, 2, 3, 4, 5]
    for i in regions:
        for j in regions:
            if i != j:
                cost[(i, j)] = params[f"cost_{i}_{j}"]

    supply = {i: params[f"supply_{i}"] for i in regions}
    demand = {i: params[f"demand_{i}"] for i in regions}

    model = gp.Model("railroad_relocation")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i,j] = number of cars moved from region i to region j
    x = {}
    for i in regions:
        for j in regions:
            if i != j:
                x[(i, j)] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"x_{i}_{j}")

    # Objective: minimize total transportation cost
    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[(i, j)] for i in regions for j in regions if i != j),
        GRB.MINIMIZE
    )

    # Flow balance constraints: for each region, supply + inflow - outflow >= demand
    for i in regions:
        inflow = gp.quicksum(x[(j, i)] for j in regions if j != i)
        outflow = gp.quicksum(x[(i, j)] for j in regions if j != i)
        model.addConstr(supply[i] + inflow - outflow >= demand[i], name=f"balance_{i}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": round(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}