import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]
    preference_weights = params["preference_weights"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    assignment_value = params["assignment_value"]

    participants = range(num_participants)
    cars = range(num_cars)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i, j] = 1 if participant i is assigned to car j
    x = {}
    for i in participants:
        for j in cars:
            if preference_weights[i][j] > 0:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Objective: maximize total assignment value
    model.setObjective(
        gp.quicksum(assignment_value * x[i, j] for (i, j) in x),
        GRB.MAXIMIZE
    )

    # Each participant assigned to at most participant_capacity cars
    for i in participants:
        assigned_vars = [x[i, j] for j in cars if (i, j) in x]
        if assigned_vars:
            model.addConstr(gp.quicksum(assigned_vars) <= participant_capacity, name=f"participant_{i}")

    # Each car assigned to at most car_capacity participants
    for j in cars:
        assigned_vars = [x[i, j] for i in participants if (i, j) in x]
        if assigned_vars:
            model.addConstr(gp.quicksum(assigned_vars) <= car_capacity, name=f"car_{j}")

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