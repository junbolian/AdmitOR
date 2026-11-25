import gurobipy as gp
from gurobipy import GRB

def solve(params):
    participants = params["participants"]
    cars = params["cars"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    preference = params["preference"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i,j] = 1 if participant i is assigned to car j
    x = {}
    for i in range(participants):
        for j in range(cars):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    model.update()

    # Objective: maximize total assignments
    model.setObjective(
        gp.quicksum(x[i, j] for i in range(participants) for j in range(cars)),
        GRB.MAXIMIZE
    )

    # Preference constraint: only assign if participant expressed interest
    for i in range(participants):
        for j in range(cars):
            if preference[i][j] == 0:
                model.addConstr(x[i, j] == 0, name=f"pref_{i}_{j}")

    # Each participant assigned to at most participant_capacity cars
    for i in range(participants):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(cars)) <= participant_capacity,
            name=f"part_cap_{i}"
        )

    # Each car assigned to at most car_capacity participants
    for j in range(cars):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(participants)) <= car_capacity,
            name=f"car_cap_{j}"
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