import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n_participants = 7
    n_cars = 7

    preferences = [
        params["preference_P0"],
        params["preference_P1"],
        params["preference_P2"],
        params["preference_P3"],
        params["preference_P4"],
        params["preference_P5"],
        params["preference_P6"],
    ]

    model = gp.Model("carpool_matching")
    model.setParam("OutputFlag", 0)

    # x[i][j] = 1 if participant i is assigned to car j
    x = {}
    for i in range(n_participants):
        for j in range(n_cars):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Objective: maximize total assignments
    model.setObjective(
        gp.quicksum(x[i, j] for i in range(n_participants) for j in range(n_cars)),
        GRB.MAXIMIZE
    )

    # Preference constraints: can only assign if participant is interested
    for i in range(n_participants):
        for j in range(n_cars):
            if preferences[i][j] == 0:
                model.addConstr(x[i, j] == 0, name=f"pref_{i}_{j}")

    # Each participant assigned to at most one car
    for i in range(n_participants):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_cars)) <= 1,
            name=f"one_car_per_participant_{i}"
        )

    # Each car assigned to at most one participant
    for j in range(n_cars):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n_participants)) <= 1,
            name=f"one_participant_per_car_{j}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}