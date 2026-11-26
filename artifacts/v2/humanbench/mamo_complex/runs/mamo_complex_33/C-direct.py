import gurobipy as gp
from gurobipy import GRB


def solve(params):
    n = 5
    cities = list(range(1, n + 1))

    # Read costs from params
    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[i, j] = params["cost_{}_{}".format(i, j)]

    model = gp.Model("tsp")
    model.Params.OutputFlag = 0

    x = model.addVars(cities, cities, vtype=GRB.BINARY, name="x")

    # Degree constraints: enter and leave each city exactly once
    for i in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for j in cities if j != i) == 1
        )
        model.addConstr(
            gp.quicksum(x[j, i] for j in cities if j != i) == 1
        )

    # MTZ subtour elimination
    u = model.addVars(cities, lb=1, ub=n - 1, vtype=GRB.CONTINUOUS, name="u")
    for i in cities:
        for j in cities:
            if i != j and i != 1 and j != 1:
                model.addConstr(
                    u[i] - u[j] + n * x[i, j] <= n - 1
                )

    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE,
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": "no_solution"}