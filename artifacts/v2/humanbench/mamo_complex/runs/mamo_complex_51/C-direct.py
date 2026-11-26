import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]

    n = 6
    regions = list(range(1, n + 1))

    cost = {}
    for i in regions:
        for j in regions:
            if i != j:
                key = f"cost_{i}_to_{j}"
                cost[(i, j)] = params[key]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = {}
    for i in regions:
        for j in regions:
            if i != j:
                x[(i, j)] = model.addVar(lb=0.0, name=f"x_{i}_{j}")

    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[(i, j)] for i in regions for j in regions if i != j),
        GRB.MINIMIZE
    )

    # Each region's net position must meet demand (surplus is allowed)
    for r in regions:
        inflow = gp.quicksum(x[(i, r)] for i in regions if i != r)
        outflow = gp.quicksum(x[(r, j)] for j in regions if j != r)
        model.addConstr(
            supply[r - 1] + inflow - outflow >= demand[r - 1],
            name=f"balance_{r}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}