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

    x = {}
    for src in cities:
        for dst in cities:
            if src != dst:
                x[(src, dst)] = model.addVar(vtype=GRB.BINARY, name=f"x_{src}_{dst}")

    # Subtour elimination variables (MTZ)
    u = {}
    for c in cities:
        u[c] = model.addVar(lb=0, ub=n - 1, vtype=GRB.CONTINUOUS, name=f"u_{c}")

    model.setObjective(
        gp.quicksum(cost[(src, dst)] * x[(src, dst)] for src in cities for dst in cities if src != dst),
        GRB.MINIMIZE
    )

    # Each city is departed exactly once
    for src in cities:
        model.addConstr(
            gp.quicksum(x[(src, dst)] for dst in cities if dst != src) == 1,
            name=f"depart_{src}"
        )

    # Each city is arrived at exactly once
    for dst in cities:
        model.addConstr(
            gp.quicksum(x[(src, dst)] for src in cities if src != dst) == 1,
            name=f"arrive_{dst}"
        )

    # MTZ subtour elimination
    # Fix u for the first city to break symmetry
    model.addConstr(u[cities[0]] == 0, name="u_start")

    for src in cities[1:]:
        for dst in cities[1:]:
            if src != dst:
                model.addConstr(
                    u[src] - u[dst] + n * x[(src, dst)] <= n - 1,
                    name=f"mtz_{src}_{dst}"
                )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}