import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 6
    cities = list(range(n))

    # Build cost matrix from params
    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[i, j] = params[f"cost_{i}_{j}"]

    pos_lb = params["pos_lower_bound"]
    pos_ub = params["pos_upper_bound"]
    pos_0_fixed = params["pos_0_fixed"]
    subtour_min = params["subtour_separation_min"]

    model = gp.Model("TSP_6cities")
    model.setParam("OutputFlag", 0)

    # Binary route variables x[i,j] = 1 if we travel from i to j
    x = {}
    for i in cities:
        for j in cities:
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Position variables for subtour elimination (MTZ-style)
    pos = {}
    for i in cities:
        pos[i] = model.addVar(lb=pos_lb, ub=pos_ub, vtype=GRB.CONTINUOUS, name=f"pos_{i}")

    model.update()

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    # Each city has exactly one outgoing route
    for i in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for j in cities if j != i) == 1,
            name=f"out_{i}"
        )

    # Each city has exactly one incoming route
    for j in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for i in cities if i != j) == 1,
            name=f"in_{j}"
        )

    # Fix position of city 0
    model.addConstr(pos[0] == pos_0_fixed, name="pos_fix_0")

    # MTZ subtour elimination constraints
    # If x[i,j] = 1 and i != 0 and j != 0, then pos[i] - pos[j] <= -1
    # Generalized: pos[i] - pos[j] + (pos_ub - pos_lb + 1) * x[i,j] <= pos_ub - pos_lb
    # Using the standard big-M form: pos[i] - pos[j] + M*x[i,j] <= M - 1
    # where M = n (number of cities)
    M = n
    for i in cities:
        for j in cities:
            if i != j and j != 0:
                model.addConstr(
                    pos[i] - pos[j] + M * x[i, j] <= M + subtour_min,
                    name=f"subtour_{i}_{j}"
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