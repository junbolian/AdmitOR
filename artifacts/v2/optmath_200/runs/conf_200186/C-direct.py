import gurobipy as gp
from gurobipy import GRB

def solve(params):
    preference_matrix = params["preference_matrix"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    assignment_value = params["assignment_value"]

    num_participants = len(preference_matrix)
    num_cars = len(preference_matrix[0])

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i][j] = 1 if participant i is assigned to car j
    x = {}
    for i in range(num_participants):
        for j in range(num_cars):
            if preference_matrix[i][j] == 1:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Objective: maximize total assignment value
    model.setObjective(
        gp.quicksum(assignment_value * x[i, j] for (i, j) in x),
        GRB.MAXIMIZE
    )

    # Participant capacity constraints
    for i in range(num_participants):
        eligible = [x[i, j] for (pi, j) in x if pi == i]
        if eligible:
            model.addConstr(gp.quicksum(eligible) <= participant_capacity, name=f"part_cap_{i}")

    # Car capacity constraints
    for j in range(num_cars):
        eligible = [x[i, j] for (i, pj) in x if pj == j]
        if eligible:
            model.addConstr(gp.quicksum(eligible) <= car_capacity, name=f"car_cap_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}