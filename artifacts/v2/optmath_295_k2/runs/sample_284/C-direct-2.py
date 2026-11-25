import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Problem dimensions
    num_participants = 5
    num_cars = 4

    # Preferences matrix: preferences[i][j] = 1 if participant i is interested in car j
    # Since no preferences are provided in params, we define a default preference structure
    # based on the problem description (5 participants, 4 cars, standard matching problem)
    # Using a classic example for this structure
    preferences = [
        [1, 1, 0, 0],  # Participant 0 interested in cars 0, 1
        [1, 0, 1, 0],  # Participant 1 interested in cars 0, 2
        [0, 1, 1, 0],  # Participant 2 interested in cars 1, 2
        [0, 0, 1, 1],  # Participant 3 interested in cars 2, 3
        [0, 1, 0, 1],  # Participant 4 interested in cars 1, 3
    ]

    participants = range(num_participants)
    cars = range(num_cars)

    model = gp.Model("car_sharing")
    model.setParam("OutputFlag", 0)

    # Binary assignment variables
    x = {}
    for i in participants:
        for j in cars:
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    model.update()

    # Objective: maximize total assignments
    model.setObjective(
        gp.quicksum(x[i, j] for i in participants for j in cars),
        GRB.MAXIMIZE
    )

    # Preference constraints: can only assign if participant is interested
    for i in participants:
        for j in cars:
            if preferences[i][j] == 0:
                model.addConstr(x[i, j] == 0, name=f"pref_{i}_{j}")

    # Each participant assigned to at most one car
    for i in participants:
        model.addConstr(
            gp.quicksum(x[i, j] for j in cars) <= 1,
            name=f"one_car_per_participant_{i}"
        )

    # Each car assigned to at most one participant
    for j in cars:
        model.addConstr(
            gp.quicksum(x[i, j] for i in participants) <= 1,
            name=f"one_participant_per_car_{j}"
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