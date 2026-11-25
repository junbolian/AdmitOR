import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = int(params["n_cities"])
    max_pos = params["max_position"]

    # Build cost dict from params
    cost = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                key = f"c_{i}_{j}"
                cost[(i, j)] = params[key]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary route variables
    x = model.addVars(
        [(i, j) for i in range(n) for j in range(n) if i != j],
        vtype=GRB.BINARY,
        name="x"
    )

    # Position variables for MTZ subtour elimination (u[0] fixed at 0)
    u = model.addVars(n, lb=0, ub=max_pos, vtype=GRB.CONTINUOUS, name="u")

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[i, j] for i in range(n) for j in range(n) if i != j),
        GRB.MINIMIZE
    )

    # Each city is arrived at exactly once
    for j in range(n):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n) if i != j) == 1,
            name=f"arrive_{j}"
        )

    # Each city is departed from exactly once
    for i in range(n):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n) if i != j) == 1,
            name=f"depart_{i}"
        )

    # Fix position of city 0
    model.addConstr(u[0] == 0, name="pos_start")

    # MTZ subtour elimination constraints for non-depot cities
    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                model.addConstr(
                    u[i] - u[j] + max_pos * x[i, j] <= max_pos - 1,
                    name=f"mtz_{i}_{j}"
                )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}