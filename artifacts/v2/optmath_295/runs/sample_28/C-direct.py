import gurobipy as gp
from gurobipy import GRB

def solve(params):
    car_capacity = params["car_capacity"]
    participant_assignment_limit = params["participant_assignment_limit"]

    # Preference list: (participant, car) pairs
    preferences = [
        (0, 2),
        (1, 0),
        (2, 0),
        (2, 1),
        (3, 1),
        (4, 1),
        (6, 3),
    ]

    num_participants = 7
    num_cars = 6

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: x[p, c] = 1 if participant p is assigned to car c
    x = {}
    for (p, c) in preferences:
        x[p, c] = model.addVar(vtype=GRB.BINARY, name=f"x_{p}_{c}")

    # Objective: maximize total assignments
    model.setObjective(gp.quicksum(x[p, c] for (p, c) in preferences), GRB.MAXIMIZE)

    # Each car can accommodate at most car_capacity participants
    for c in range(num_cars):
        car_vars = [x[p, cc] for (p, cc) in preferences if cc == c]
        if car_vars:
            model.addConstr(gp.quicksum(car_vars) <= car_capacity, name=f"car_cap_{c}")

    # Each participant can be assigned to at most participant_assignment_limit cars
    for p in range(num_participants):
        p_vars = [x[pp, c] for (pp, c) in preferences if pp == p]
        if p_vars:
            model.addConstr(gp.quicksum(p_vars) <= participant_assignment_limit, name=f"part_limit_{p}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}