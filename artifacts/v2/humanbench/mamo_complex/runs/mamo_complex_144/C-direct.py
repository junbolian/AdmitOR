import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = params["cost"]
    n = len(cost)
    cities = range(n)

    model = gp.Model("tsp")
    model.Params.OutputFlag = 0

    x = model.addVars(cities, cities, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE,
    )

    for i in cities:
        model.addConstr(gp.quicksum(x[i, j] for j in cities if j != i) == 1)
        model.addConstr(gp.quicksum(x[j, i] for j in cities if j != i) == 1)
    for i in cities:
        model.addConstr(x[i, i] == 0)

    # Subtour elimination (lazy via callbacks is overkill for n=5; add full formulation)
    from itertools import combinations
    for r in range(2, n):
        for S in combinations(cities, r):
            model.addConstr(
                gp.quicksum(x[i, j] for i in S for j in S if i != j) <= len(S) - 1
            )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    return {"objective": None, "status": "infeasible"}