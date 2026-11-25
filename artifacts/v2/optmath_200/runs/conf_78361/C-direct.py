import gurobipy as gp
from gurobipy import GRB

def solve(params):
    assignment_value = params["assignment_value"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    preference = params["preference"]

    num_participants = len(preference)
    num_cars = len(preference[0])

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i][j] = 1 if participant i is assigned to car j
    x = {}
    for i in range(num_participants):
        for j in range(num_cars):
            if preference[i][j] == 1:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Objective: maximize total assignments
    model.setObjective(
        gp.quicksum(assignment_value * x[i, j] for (i, j) in x),
        GRB.MAXIMIZE
    )

    # Each participant assigned to at most participant_capacity cars
    for i in range(num_participants):
        vars_i = [x[i, j] for (pi, j) in x if pi == i]
        if vars_i:
            model.addConstr(gp.quicksum(vars_i) <= participant_capacity, name=f"part_{i}")

    # Each car assigned to at most car_capacity participants
    for j in range(num_cars):
        vars_j = [x[i, j] for (i, pj) in x if pj == j]
        if vars_j:
            model.addConstr(gp.quicksum(vars_j) <= car_capacity, name=f"car_{j}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{status}"}