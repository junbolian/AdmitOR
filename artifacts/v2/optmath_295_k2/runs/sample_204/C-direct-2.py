import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    cost = params["cost"]
    capacity = params["capacity"]

    n = len(supply)
    cities = range(n)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: flow from i to j (skip diagonal)
    x = {}
    for i in cities:
        for j in cities:
            if i != j:
                x[i, j] = model.addVar(lb=0.0, ub=capacity[i][j], name=f"x_{i}_{j}")

    model.update()

    # Objective: minimize total transportation cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    # Flow balance constraints: outflow - inflow = supply[i]
    for i in cities:
        outflow = gp.quicksum(x[i, j] for j in cities if j != i)
        inflow = gp.quicksum(x[j, i] for j in cities if j != i)
        model.addConstr(outflow - inflow == supply[i], name=f"balance_{i}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}