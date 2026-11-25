import gurobipy as gp
from gurobipy import GRB


def solve(params):
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]
    assignment_value = params["assignment_value"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    preference_matrix = params["preference_matrix"]

    participants = range(num_participants)
    cars = range(num_cars)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary assignment variables, only where participant is eligible
    x = {}
    for i in participants:
        for j in cars:
            if preference_matrix[i][j] == 1:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Objective: maximize total assignments
    model.setObjective(
        gp.quicksum(assignment_value * x[i, j] for (i, j) in x),
        GRB.MAXIMIZE
    )

    # Each participant assigned to at most participant_capacity cars
    for i in participants:
        eligible = [x[i, j] for j in cars if (i, j) in x]
        if eligible:
            model.addConstr(gp.quicksum(eligible) <= participant_capacity, name=f"part_{i}")

    # Each car assigned to at most car_capacity participants
    for j in cars:
        eligible = [x[i, j] for i in participants if (i, j) in x]
        if eligible:
            model.addConstr(gp.quicksum(eligible) <= car_capacity, name=f"car_{j}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}