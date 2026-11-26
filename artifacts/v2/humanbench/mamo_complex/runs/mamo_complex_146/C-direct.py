import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cities = ["Alpha", "Bravo", "Charlie", "Delta"]
    n = len(cities)

    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[(i, j)] = params["cost_{}_{}".format(i, j)]

    model = gp.Model("tsp")
    model.Params.OutputFlag = 0

    x = {}
    for i in cities:
        for j in cities:
            if i != j:
                x[(i, j)] = model.addVar(vtype=GRB.BINARY, name="x_%s_%s" % (i, j))

    u = {}
    for i in cities:
        u[i] = model.addVar(lb=0, ub=n - 1, vtype=GRB.CONTINUOUS, name="u_%s" % i)

    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[(i, j)] for (i, j) in x), GRB.MINIMIZE
    )

    for j in cities:
        model.addConstr(
            gp.quicksum(x[(i, j)] for i in cities if i != j) == 1,
            name="in_%s" % j,
        )
    for i in cities:
        model.addConstr(
            gp.quicksum(x[(i, j)] for j in cities if j != i) == 1,
            name="out_%s" % i,
        )

    # MTZ subtour elimination
    for i in cities:
        for j in cities:
            if i != j and i != cities[0] and j != cities[0]:
                model.addConstr(
                    u[i] - u[j] + n * x[(i, j)] <= n - 1,
                    name="mtz_%s_%s" % (i, j),
                )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "failed"}