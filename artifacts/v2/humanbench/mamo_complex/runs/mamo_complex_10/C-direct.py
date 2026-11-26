import gurobipy as gp
from gurobipy import GRB

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
    n = len(cities)
    arcs = list(cost.keys())

    model = gp.Model("TSP_4cities")
    model.setParam("OutputFlag", 0)

    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")

    # Subtour elimination via MTZ
    # u[i] is the position of city i in the tour (continuous, for i != 1)
    u = model.addVars(cities, lb=1.0, ub=n, vtype=GRB.CONTINUOUS, name="u")

    model.setObjective(gp.quicksum(cost[i, j] * x[i, j] for (i, j) in arcs), GRB.MINIMIZE)

    # Each city must be left exactly once
    for i in cities:
        model.addConstr(gp.quicksum(x[i, j] for j in cities if (i, j) in cost) == 1, name=f"leave_{i}")

    # Each city must be entered exactly once
    for j in cities:
        model.addConstr(gp.quicksum(x[i, j] for i in cities if (i, j) in cost) == 1, name=f"enter_{j}")

    # MTZ subtour elimination constraints (for i != 1, j != 1, i != j)
    for i in cities:
        for j in cities:
            if i != j and i != 1 and j != 1 and (i, j) in cost:
                model.addConstr(u[i] - u[j] + n * x[i, j] <= n - 1, name=f"mtz_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}