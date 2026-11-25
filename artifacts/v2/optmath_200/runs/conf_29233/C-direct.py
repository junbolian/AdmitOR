import gurobipy as gp
from gurobipy import GRB

def solve(params):
    preference_edge_value = params["preference_edge_value"]

    # Structural constants (set sizes and preference structure)
    num_participants = 7
    num_cars = 5

    # Allowed (participant, car) pairs based on preferences
    allowed_edges = [
        (1, 1),
        (2, 0), (2, 3), (2, 4),
        (3, 0),
        (4, 1), (4, 3),
    ]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary assignment variables only for allowed edges
    x = {}
    for (p, c) in allowed_edges:
        x[p, c] = model.addVar(vtype=GRB.BINARY, name=f"x_{p}_{c}")

    # Objective: maximize total assignments
    model.setObjective(
        gp.quicksum(preference_edge_value * x[p, c] for (p, c) in allowed_edges),
        GRB.MAXIMIZE
    )

    # Each participant assigned to at most one car
    for participant in range(num_participants):
        participant_vars = [x[p, c] for (p, c) in allowed_edges if p == participant]
        if participant_vars:
            model.addConstr(gp.quicksum(participant_vars) <= 1, name=f"one_car_per_participant_{participant}")

    # Each car assigned to at most one participant
    for car in range(num_cars):
        car_vars = [x[p, c] for (p, c) in allowed_edges if c == car]
        if car_vars:
            model.addConstr(gp.quicksum(car_vars) <= 1, name=f"one_participant_per_car_{car}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}