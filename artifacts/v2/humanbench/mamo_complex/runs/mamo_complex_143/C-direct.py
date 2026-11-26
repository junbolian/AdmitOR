import gurobipy as gp
from gurobipy import GRB
import itertools

def solve(params):
    c12 = params["c12"]
    c13 = params["c13"]
    c14 = params["c14"]
    c21 = params["c21"]
    c23 = params["c23"]
    c24 = params["c24"]
    c31 = params["c31"]
    c32 = params["c32"]
    c34 = params["c34"]
    c41 = params["c41"]
    c42 = params["c42"]
    c43 = params["c43"]

    n = 4
    cities = [1, 2, 3, 4]

    cost = {
        (1, 2): c12, (1, 3): c13, (1, 4): c14,
        (2, 1): c21, (2, 3): c23, (2, 4): c24,
        (3, 1): c31, (3, 2): c32, (3, 4): c34,
        (4, 1): c41, (4, 2): c42, (4, 3): c43,
    }

    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = gp.Model("TSP4")
    model.setParam("OutputFlag", 0)

    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")

    model.setObjective(gp.quicksum(cost[i, j] * x[i, j] for i, j in arcs), GRB.MINIMIZE)

    # Each city must be left exactly once
    for i in cities:
        model.addConstr(gp.quicksum(x[i, j] for j in cities if j != i) == 1, name=f"leave_{i}")

    # Each city must be entered exactly once
    for j in cities:
        model.addConstr(gp.quicksum(x[i, j] for i in cities if i != j) == 1, name=f"enter_{j}")

    # Subtour elimination via MTZ
    u = model.addVars(cities, lb=0.0, ub=n - 1, vtype=GRB.CONTINUOUS, name="u")

    for i in cities:
        for j in cities:
            if i != j and j != 1:
                model.addConstr(u[i] - u[j] + n * x[i, j] <= n - 1, name=f"mtz_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}