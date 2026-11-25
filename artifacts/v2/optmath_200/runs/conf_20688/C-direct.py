import gurobipy as gp
from gurobipy import GRB

def solve(params):
    preferences = params["participant_preferences"]
    car_capacity = params["car_capacity"]
    participant_capacity = params["participant_capacity"]
    assignment_value = params["assignment_value"]

    num_participants = len(preferences)
    num_cars = len(car_capacity)

    model = gp.Model("car_assignment")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i, j] = 1 if participant i is assigned to car j
    x = {}
    for i in range(num_participants):
        pref_row = preferences[i]
        for j in range(num_cars):
            # pref_row may be shorter than num_cars if participant has no interest in higher-indexed cars
            if j < len(pref_row) and pref_row[j] == 1:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Objective: maximize total assignment value
    model.setObjective(
        gp.quicksum(assignment_value * x[i, j] for (i, j) in x),
        GRB.MAXIMIZE
    )

    # Participant capacity constraint: each participant assigned to at most participant_capacity cars
    for i in range(num_participants):
        eligible = [x[i, j] for (pi, j) in x if pi == i]
        if eligible:
            model.addConstr(gp.quicksum(eligible) <= participant_capacity, name=f"part_cap_{i}")

    # Car capacity constraint: each car assigned to at most car_capacity[j] participants
    for j in range(num_cars):
        eligible = [x[i, j] for (i, pj) in x if pj == j]
        if eligible:
            model.addConstr(gp.quicksum(eligible) <= car_capacity[j], name=f"car_cap_{j}")

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