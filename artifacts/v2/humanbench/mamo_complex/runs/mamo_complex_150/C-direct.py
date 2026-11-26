import gurobipy as gp
from gurobipy import GRB


def solve(params):
    n = params["num_cities"]
    cities = ["E", "F", "G", "H", "I"]
    # sanity: index-set size is structural, but respect num_cities if smaller
    if n != len(cities):
        return {"objective": None, "status": "size mismatch"}

    cost = {}
    for a in cities:
        for b in cities:
            if a != b:
                cost[(a, b)] = params["cost_{}_{}".format(a, b)]

    model = gp.Model("courier_tsp")
    model.Params.OutputFlag = 0

    x = model.addVars(cities, cities, vtype=GRB.BINARY, name="x")

    # enter each city exactly once
    for b in cities:
        model.addConstr(
            gp.quicksum(x[a, b] for a in cities if a != b) == 1
        )
    # leave each city exactly once
    for a in cities:
        model.addConstr(
            gp.quicksum(x[a, b] for b in cities if b != a) == 1
        )

    # MTZ subtour elimination
    u = model.addVars(cities, vtype=GRB.CONTINUOUS, lb=0, ub=n - 1, name="u")
    for a in cities:
        for b in cities:
            if a != b and a != cities[0] and b != cities[0]:
                model.addConstr(
                    u[a] - u[b] + n * x[a, b] <= n - 1
                )

    model.setObjective(
        gp.quicksum(cost[(a, b)] * x[a, b] for a in cities for b in cities if a != b),
        GRB.MINIMIZE,
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    return {"objective": None, "status": "no optimal solution"}