import gurobipy as gp
from gurobipy import GRB

def solve(params):
    preferences = params["preferences"]
    num_participants = len(preferences)
    num_cars = len(preferences[0])

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i][j] = 1 if participant i is assigned to car j
    x = [
        [
            model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")
            for j in range(num_cars)
        ]
        for i in range(num_participants)
    ]

    # Objective: maximize total assignments
    model.setObjective(
        gp.quicksum(x[i][j] for i in range(num_participants) for j in range(num_cars)),
        GRB.MAXIMIZE
    )

    # Preference constraints: can only assign if interested
    for i in range(num_participants):
        for j in range(num_cars):
            if preferences[i][j] == 0:
                model.addConstr(x[i][j] == 0, name=f"pref_{i}_{j}")

    # Each participant assigned to at most one car
    for i in range(num_participants):
        model.addConstr(
            gp.quicksum(x[i][j] for j in range(num_cars)) <= 1,
            name=f"one_car_per_participant_{i}"
        )

    # Each car assigned to at most one participant
    for j in range(num_cars):
        model.addConstr(
            gp.quicksum(x[i][j] for i in range(num_participants)) <= 1,
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