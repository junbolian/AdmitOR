import gurobipy as gp
from gurobipy import GRB

def solve(params):
    preference = params["preference"]
    assignment_value = params["assignment_value"]

    n_participants = 6
    n_cars = 6

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i][j] = 1 if participant i assigned to car j
    x = {}
    for i in range(n_participants):
        for j in range(n_cars):
            if preference[i][j] == 1:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Objective: maximize total assignments
    model.setObjective(
        gp.quicksum(assignment_value * x[i, j] for (i, j) in x),
        GRB.MAXIMIZE
    )

    # Each participant assigned to at most one car
    for i in range(n_participants):
        eligible = [(i, j) for j in range(n_cars) if (i, j) in x]
        if eligible:
            model.addConstr(gp.quicksum(x[i, j] for (_, j) in eligible) <= 1)

    # Each car assigned to at most one participant
    for j in range(n_cars):
        eligible = [(i, j) for i in range(n_participants) if (i, j) in x]
        if eligible:
            model.addConstr(gp.quicksum(x[i, j] for (i, _) in eligible) <= 1)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}