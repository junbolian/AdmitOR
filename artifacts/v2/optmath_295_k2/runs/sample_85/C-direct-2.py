import gurobipy as gp
from gurobipy import GRB

def solve(params):
    preference_matrix = params["preference_matrix"]
    unit_assignment_value = params["unit_assignment_value"]

    num_participants = len(preference_matrix)
    num_cars = len(preference_matrix[0])

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary assignment variables: x[p][c] = 1 if participant p assigned to car c
    x = {
        (p, c): model.addVar(vtype=GRB.BINARY, name=f"x_{p}_{c}")
        for p in range(num_participants)
        for c in range(num_cars)
        if preference_matrix[p][c] == 1
    }

    # Objective: maximize total assignments weighted by unit_assignment_value
    model.setObjective(
        gp.quicksum(unit_assignment_value * x[p, c] for (p, c) in x),
        GRB.MAXIMIZE
    )

    # Each participant assigned to at most one car
    for p in range(num_participants):
        eligible = [(p, c) for c in range(num_cars) if (p, c) in x]
        if eligible:
            model.addConstr(gp.quicksum(x[p, c] for (p, c) in eligible) <= 1)

    # Each car assigned to at most one participant
    for c in range(num_cars):
        eligible = [(p, c) for p in range(num_participants) if (p, c) in x]
        if eligible:
            model.addConstr(gp.quicksum(x[p, c] for (p, c) in eligible) <= 1)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}