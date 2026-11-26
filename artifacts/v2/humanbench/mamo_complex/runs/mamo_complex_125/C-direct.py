import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]

    # Build cost matrix: cost[i][j] for i != j (1-indexed, stored as 0-indexed)
    # Regions 1..6 -> indices 0..5
    n = 6
    cost = {}
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if i != j:
                key = f"cost_{i}_{j}"
                cost[(i, j)] = params[key]

    model = gp.Model("food_distribution")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i,j] = tons shipped from region i to region j
    x = {}
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if i != j:
                x[(i, j)] = model.addVar(lb=0.0, name=f"x_{i}_{j}")

    # Objective: minimize total transport cost
    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[(i, j)] for i in range(1, n + 1) for j in range(1, n + 1) if i != j),
        GRB.MINIMIZE
    )

    # Supply constraints: food shipped out from region i <= supply[i-1] - (demand[i-1] - supply[i-1]) if surplus
    # Flow balance: supply[i] + inflow[i] - outflow[i] >= demand[i]
    for i in range(1, n + 1):
        inflow = gp.quicksum(x[(j, i)] for j in range(1, n + 1) if j != i)
        outflow = gp.quicksum(x[(i, j)] for j in range(1, n + 1) if j != i)
        # Net available after transfers must meet demand
        model.addConstr(
            supply[i - 1] + inflow - outflow >= demand[i - 1],
            name=f"demand_{i}"
        )
        # Cannot ship out more than available supply
        model.addConstr(
            outflow <= supply[i - 1],
            name=f"supply_{i}"
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