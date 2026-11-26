import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cities = ['E', 'F', 'G', 'H', 'I']
    n = len(cities)
    idx = {c: i for i, c in enumerate(cities)}

    cost = {}
    for src in cities:
        for dst in cities:
            if src != dst:
                key = f"cost_{src}_{dst}"
                cost[(src, dst)] = params[key]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    x = model.addVars(cities, cities, vtype=GRB.BINARY, name="x")

    # No self-loops
    for c in cities:
        model.addConstr(x[c, c] == 0)

    # Each city is left exactly once
    for src in cities:
        model.addConstr(gp.quicksum(x[src, dst] for dst in cities if dst != src) == 1)

    # Each city is entered exactly once
    for dst in cities:
        model.addConstr(gp.quicksum(x[src, dst] for src in cities if src != dst) == 1)

    # Subtour elimination via MTZ
    u = model.addVars(cities, vtype=GRB.CONTINUOUS, name="u")
    for src in cities:
        for dst in cities:
            if src != dst and dst != cities[0]:
                model.addConstr(u[src] - u[dst] + n * x[src, dst] <= n - 1)

    model.setObjective(
        gp.quicksum(cost[(src, dst)] * x[src, dst] for src in cities for dst in cities if src != dst),
        GRB.MINIMIZE
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}