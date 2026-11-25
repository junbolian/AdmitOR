import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]
    interest = params["participant_car_interest"]
    max_participant_assignments = params["max_participant_assignments"]
    max_car_assignments = params["max_car_assignments"]

    participants = range(num_participants)
    cars = range(num_cars)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: x[p, c] = 1 if participant p is assigned to car c
    x = {}
    for p in participants:
        for c in cars:
            if interest[p][c] == 1:
                x[p, c] = model.addVar(vtype=GRB.BINARY, name=f"x_{p}_{c}")

    # Objective: maximize total assignments
    model.setObjective(gp.quicksum(x[p, c] for (p, c) in x), GRB.MAXIMIZE)

    # Each participant assigned to at most max_participant_assignments cars
    for p in participants:
        assigned_vars = [x[p, c] for c in cars if (p, c) in x]
        if assigned_vars:
            model.addConstr(gp.quicksum(assigned_vars) <= max_participant_assignments)

    # Each car assigned to at most max_car_assignments participants
    for c in cars:
        assigned_vars = [x[p, c] for p in participants if (p, c) in x]
        if assigned_vars:
            model.addConstr(gp.quicksum(assigned_vars) <= max_car_assignments)

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