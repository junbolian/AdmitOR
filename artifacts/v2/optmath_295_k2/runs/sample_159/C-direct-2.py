import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 5
    cities = list(range(n))

    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[i, j] = params[f"cost_{i}_{j}"]

    model = gp.Model("tsp")
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if we travel from city i to city j
    x = model.addVars(
        [(i, j) for i in cities for j in cities if i != j],
        vtype=GRB.BINARY,
        name="x"
    )

    # u[i] = position of city i in the tour (MTZ formulation), for i in 1..4
    u = model.addVars(
        [i for i in cities if i != 0],
        vtype=GRB.CONTINUOUS,
        lb=1,
        ub=n - 1,
        name="u"
    )

    # Objective
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    # Each city is departed exactly once
    for i in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for j in cities if j != i) == 1,
            name=f"depart_{i}"
        )

    # Each city is arrived at exactly once
    for j in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for i in cities if i != j) == 1,
            name=f"arrive_{j}"
        )

    # MTZ subtour elimination: for i != 0, j != 0, i != j
    # u[j] >= u[i] + 1 - (n-1)*(1 - x[i,j])
    for i in cities:
        for j in cities:
            if i != j and i != 0 and j != 0:
                model.addConstr(
                    u[j] >= u[i] + 1 - (n - 1) * (1 - x[i, j]),
                    name=f"mtz_{i}_{j}"
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