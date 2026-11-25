import gurobipy as gp
from gurobipy import GRB
from itertools import product as iproduct


def solve(params):
    cost = params["cost"]
    n = 5
    cities = range(n)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if we travel from city i to city j
    x = {}
    for i in cities:
        for j in cities:
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # u[i] = position of city i in the tour (MTZ formulation), for i in 1..4
    u = {}
    for i in cities:
        if i != 0:
            u[i] = model.addVar(lb=1, ub=n - 1, vtype=GRB.CONTINUOUS, name=f"u_{i}")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in cities for j in cities if i != j),
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

    # MTZ subtour elimination: if x[i,j]=1 and both i,j != 0, then u[j] >= u[i] + 1
    big_m = n - 1
    for i in cities:
        for j in cities:
            if i != j and i != 0 and j != 0:
                model.addConstr(
                    u[j] >= u[i] + 1 - big_m * (1 - x[i, j]),
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