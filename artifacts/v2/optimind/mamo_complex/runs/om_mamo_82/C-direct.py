import gurobipy as gp
from gurobipy import GRB
from itertools import combinations

def solve(params):
    cost = {
        (1, 2): params["cost_12"],
        (1, 3): params["cost_13"],
        (1, 4): params["cost_14"],
        (2, 1): params["cost_21"],
        (2, 3): params["cost_23"],
        (2, 4): params["cost_24"],
        (3, 1): params["cost_31"],
        (3, 2): params["cost_32"],
        (3, 4): params["cost_34"],
        (4, 1): params["cost_41"],
        (4, 2): params["cost_42"],
        (4, 3): params["cost_43"],
    }

    n = 4
    cities = list(range(1, n + 1))
    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")

    model.setObjective(gp.quicksum(cost[i, j] * x[i, j] for (i, j) in arcs), GRB.MINIMIZE)

    # Each city is left exactly once
    for i in cities:
        model.addConstr(gp.quicksum(x[i, j] for j in cities if j != i) == 1, name=f"leave_{i}")

    # Each city is entered exactly once
    for j in cities:
        model.addConstr(gp.quicksum(x[i, j] for i in cities if i != j) == 1, name=f"enter_{j}")

    # Subtour elimination via MTZ formulation
    u = model.addVars(cities, vtype=GRB.CONTINUOUS, name="u")
    for i in cities:
        u[i].lb = 0
        u[i].ub = n - 1

    for i in cities:
        for j in cities:
            if i != j and not (i == 1 or j == 1):
                model.addConstr(u[i] - u[j] + n * x[i, j] <= n - 1, name=f"mtz_{i}_{j}")

    # Fix u[1] = 0 as the starting city
    model.addConstr(u[1] == 0, name="u_start")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}