import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]  # list of 5 values, index 0..4
    demand = params["demand"]  # list of 5 values, index 0..4
    cost   = params["cost"]    # 5x5 matrix, cost[i][j]

    n = 5
    cities = range(n)

    model = gp.Model("resource_redistribution")
    model.setParam("OutputFlag", 0)

    # x[i][j] = units transferred from city i to city j (i != j)
    x = {
        (i, j): model.addVar(lb=0.0, name=f"x_{i}_{j}")
        for i in cities
        for j in cities
        if i != j
    }

    # Objective: minimize total transfer cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    # Flow balance: supply[i] + inflow[i] - outflow[i] >= demand[i]
    for i in cities:
        inflow  = gp.quicksum(x[j, i] for j in cities if j != i)
        outflow = gp.quicksum(x[i, j] for j in cities if j != i)
        model.addConstr(
            supply[i] + inflow - outflow >= demand[i],
            name=f"balance_{i}"
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