import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = {
        (0, 1): params["cost_0_1"],
        (0, 2): params["cost_0_2"],
        (1, 0): params["cost_1_0"],
        (1, 2): params["cost_1_2"],
        (2, 0): params["cost_2_0"],
        (2, 1): params["cost_2_1"],
    }

    cities = [0, 1, 2]
    arcs = list(cost.keys())

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary decision variables: x[i,j] = 1 if arc (i,j) is used
    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")

    # Position variables for cities 1 and 2 (MTZ subtour elimination)
    u = model.addVars([1, 2], lb=0.0, ub=2.0, vtype=GRB.CONTINUOUS, name="u")

    # Objective: minimize total travel cost
    model.setObjective(gp.quicksum(cost[i, j] * x[i, j] for (i, j) in arcs), GRB.MINIMIZE)

    # Each city must be left exactly once
    for i in cities:
        model.addConstr(gp.quicksum(x[i, j] for (ii, j) in arcs if ii == i) == 1, name=f"leave_{i}")

    # Each city must be entered exactly once
    for j in cities:
        model.addConstr(gp.quicksum(x[i, j] for (i, jj) in arcs if jj == j) == 1, name=f"enter_{j}")

    # MTZ subtour elimination constraints for non-depot cities (1 and 2)
    # If arc (i,j) is used (both i,j != 0), then u[i] + 1 <= u[j]
    n = len(cities)
    for (i, j) in arcs:
        if i != 0 and j != 0:
            model.addConstr(u[i] - u[j] + n * x[i, j] <= n - 1, name=f"mtz_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}