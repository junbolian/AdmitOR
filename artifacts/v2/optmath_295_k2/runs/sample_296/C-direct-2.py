import gurobipy as gp
from gurobipy import GRB

def solve(params):
    preferences = params["preferences"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]

    num_participants = len(preferences)
    num_cars = len(preferences[0])

    model = gp.Model("carpooling")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i][j] = 1 if participant i is assigned to car j
    x = {}
    for i in range(num_participants):
        for j in range(num_cars):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    model.update()

    # Objective: maximize total assignments
    model.setObjective(
        gp.quicksum(x[i, j] for i in range(num_participants) for j in range(num_cars)),
        GRB.MAXIMIZE
    )

    # Constraint 1: Only assign if participant is interested
    for i in range(num_participants):
        for j in range(num_cars):
            model.addConstr(x[i, j] <= preferences[i][j], name=f"pref_{i}_{j}")

    # Constraint 2: Each participant assigned to at most participant_capacity[i] cars
    for i in range(num_participants):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_cars)) <= participant_capacity[i],
            name=f"part_cap_{i}"
        )

    # Constraint 3: Each car assigned to at most car_capacity[j] participants
    for j in range(num_cars):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_participants)) <= car_capacity[j],
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