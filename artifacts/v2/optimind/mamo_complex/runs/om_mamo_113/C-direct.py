import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cities = ['A', 'B', 'C', 'D', 'E']
    n = len(cities)
    idx = {c: i for i, c in enumerate(cities)}

    cost = {}
    for src in cities:
        for dst in cities:
            if src != dst:
                key = f"cost_{src}{dst}"
                cost[(src, dst)] = params[key]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if travel from city i to city j
    x = {}
    for src in cities:
        for dst in cities:
            if src != dst:
                x[(src, dst)] = model.addVar(vtype=GRB.BINARY, name=f"x_{src}_{dst}")

    # u[i] = subtour elimination variable (MTZ), u in [1, n-1] for non-depot nodes
    # We fix A as the depot (index 0) for MTZ
    u = {}
    for c in cities:
        if c != 'A':
            u[c] = model.addVar(lb=1, ub=n - 1, vtype=GRB.INTEGER, name=f"u_{c}")

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
    for src in cities:
        for dst in cities:
            if src != dst and src != 'A' and dst != 'A':
                model.addConstr(
                    u[src] - u[dst] + (n - 1) * x[(src, dst)] <= n - 2,
                    name=f"mtz_{src}_{dst}"
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