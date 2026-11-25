import gurobipy as gp
from gurobipy import GRB

def solve(params):
    preference = params["preference"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    n_participants = params["n_participants"]
    n_cars = params["n_cars"]
    objective_coeff = params["objective_coeff"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i, j] = 1 if participant i is assigned to car j
    x = {}
    for i in range(n_participants):
        for j in range(n_cars):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    model.update()

    # Objective: maximize total successful assignments
    model.setObjective(
        gp.quicksum(objective_coeff * preference[i][j] * x[i, j]
                    for i in range(n_participants)
                    for j in range(n_cars)),
        GRB.MAXIMIZE
    )

    # Each participant assigned to at most participant_capacity[i] cars
    for i in range(n_participants):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_cars)) <= participant_capacity[i],
            name=f"participant_cap_{i}"
        )

    # Each car assigned to at most car_capacity[j] participants
    for j in range(n_cars):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n_participants)) <= car_capacity[j],
            name=f"car_cap_{j}"
        )

    # Only allow assignments where preference is 1
    for i in range(n_participants):
        for j in range(n_cars):
            if preference[i][j] == 0:
                model.addConstr(x[i, j] == 0, name=f"pref_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}