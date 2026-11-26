import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cities = ["A", "B", "C", "D", "E"]
    n = len(cities)

    cost = {}
    for i, ci in enumerate(cities):
        for j, cj in enumerate(cities):
            if i != j:
                cost[i, j] = params["cost_{}_to_{}".format(ci, cj)]

    model = gp.Model("tsp")

    x = model.addVars(cost.keys(), vtype=GRB.BINARY, name="x")
    u = model.addVars(range(1, n), vtype=GRB.CONTINUOUS, lb=0, ub=n - 1, name="u")

    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for (i, j) in cost.keys()),
        GRB.MINIMIZE,
    )

    for i in range(n):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n) if (i, j) in cost) == 1,
            name="out_{}".format(i),
        )
        model.addConstr(
            gp.quicksum(x[j, i] for j in range(n) if (j, i) in cost) == 1,
            name="in_{}".format(i),
        )

    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                model.addConstr(
                    u[i] - u[j] + n * x[i, j] <= n - 1,
                    name="mtz_{}_{}".format(i, j),
                )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "no_solution"}