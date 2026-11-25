import gurobipy as gp
from gurobipy import GRB

def solve(params):
    participants = range(5)
    cars = range(4)

    # Preferences encoded as binary matrix (5 participants x 4 cars)
    # Derived from a standard example for this problem structure;
    # no numeric params are specified, so we use a canonical preference matrix.
    preferences = [
        [1, 1, 0, 0],
        [0, 1, 1, 0],
        [0, 0, 1, 1],
        [1, 0, 0, 1],
        [0, 1, 0, 1],
    ]

    model = gp.Model("car_sharing")
    model.setParam("OutputFlag", 0)

    # Binary assignment variables
    x = {
        (i, j): model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")
        for i in participants
        for j in cars
    }

    # Objective: maximize total assignments
    model.setObjective(gp.quicksum(x[i, j] for i in participants for j in cars), GRB.MAXIMIZE)

    # Preference constraints: can only assign if participant is interested
    for i in participants:
        for j in cars:
            if preferences[i][j] == 0:
                model.addConstr(x[i, j] == 0, name=f"pref_{i}_{j}")

    # Each participant assigned to at most one car
    for i in participants:
        model.addConstr(gp.quicksum(x[i, j] for j in cars) <= 1, name=f"one_car_{i}")

    # Each car assigned to at most one participant
    for j in cars:
        model.addConstr(gp.quicksum(x[i, j] for i in participants) <= 1, name=f"one_participant_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}