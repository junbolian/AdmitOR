import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cities = ['E', 'F', 'G', 'H', 'I']
    n = len(cities)
    idx = {c: i for i, c in enumerate(cities)}

    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                key = f"cost_{i}_{j}"
                cost[(i, j)] = params[key]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    x = model.addVars(
        [(i, j) for i in cities for j in cities if i != j],
        vtype=GRB.BINARY,
        name="x"
    )

    # Subtour elimination via MTZ
    u = model.addVars(cities, lb=0, ub=n - 1, vtype=GRB.CONTINUOUS, name="u")

    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    # Each city is left exactly once
    for i in cities:
        model.addConstr(gp.quicksum(x[i, j] for j in cities if j != i) == 1, name=f"leave_{i}")

    # Each city is entered exactly once
    for j in cities:
        model.addConstr(gp.quicksum(x[i, j] for i in cities if i != j) == 1, name=f"enter_{j}")

    # MTZ subtour elimination (fix u for first city)
    start = cities[0]
    model.addConstr(u[start] == 0, name="u_start")
    for i in cities:
        for j in cities:
            if i != j and j != start:
                model.addConstr(
                    u[j] >= u[i] + 1 - n * (1 - x[i, j]),
                    name=f"mtz_{i}_{j}"
                )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}