import gurobipy as gp
from gurobipy import GRB

def solve(params):
    interest = params["participant_interest"]
    max_per_participant = params["max_assignments_per_participant"]
    max_per_car = params["max_assignments_per_car"]

    num_participants = 5
    num_cars = 4

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary assignment variables, only where participant is eligible
    x = {}
    for i in range(num_participants):
        for j in range(num_cars):
            if interest[i][j] == 1:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Maximize total assignments
    model.setObjective(gp.quicksum(x[i, j] for (i, j) in x), GRB.MAXIMIZE)

    # Each participant assigned to at most max_assignments_per_participant cars
    for i in range(num_participants):
        eligible = [x[i, j] for j in range(num_cars) if (i, j) in x]
        if eligible:
            model.addConstr(gp.quicksum(eligible) <= max_per_participant, name=f"part_{i}")

    # Each car assigned to at most max_assignments_per_car participants
    for j in range(num_cars):
        eligible = [x[i, j] for i in range(num_participants) if (i, j) in x]
        if eligible:
            model.addConstr(gp.quicksum(eligible) <= max_per_car, name=f"car_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}