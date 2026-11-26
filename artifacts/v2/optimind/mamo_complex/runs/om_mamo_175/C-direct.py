import gurobipy as gp
from gurobipy import GRB
from itertools import permutations

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

    cities = [1, 2, 3, 4]
    arcs = list(cost.keys())

    model = gp.Model("TSP_4cities")
    model.setParam("OutputFlag", 0)

    # Binary variables: x[i,j] = 1 if arc (i,j) is used
    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")

    # Objective: minimize total travel cost
    model.setObjective(gp.quicksum(cost[i, j] * x[i, j] for (i, j) in arcs), GRB.MINIMIZE)

    # Each city is left exactly once
    for i in cities:
        model.addConstr(gp.quicksum(x[i, j] for (ii, j) in arcs if ii == i) == 1, name=f"leave_{i}")

    # Each city is entered exactly once
    for j in cities:
        model.addConstr(gp.quicksum(x[i, j] for (i, jj) in arcs if jj == j) == 1, name=f"enter_{j}")

    # Subtour elimination via MTZ formulation
    # u[i] is a continuous variable representing position in tour (for i != 1)
    n = len(cities)
    u = model.addVars(cities, lb=0, ub=n - 1, vtype=GRB.CONTINUOUS, name="u")

    # Fix position of city 1
    model.addConstr(u[1] == 0, name="u_start")

    # MTZ constraints: for each arc (i,j) where neither is the depot (or we include all)
    for (i, j) in arcs:
        if j != 1:  # skip arcs returning to city 1
            model.addConstr(
                u[i] - u[j] + n * x[i, j] <= n - 1,
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