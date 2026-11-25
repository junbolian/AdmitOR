import gurobipy as gp
from gurobipy import GRB

def solve(params):
    assignment_value = params["assignment_value"]

    # Preference matrix: preferences[i][j] = 1 if participant i is interested in car j
    preferences = {
        0: {2: 1, 4: 1},
        1: {},
        2: {0: 1, 4: 1},
        3: {0: 1, 4: 1},
    }

    participants = range(4)
    cars = range(5)

    # Valid (participant, car) pairs based on preferences
    valid_pairs = [
        (i, j)
        for i in participants
        for j in cars
        if preferences[i].get(j, 0) == 1
    ]

    model = gp.Model("carpooling")
    model.setParam("OutputFlag", 0)

    # Binary decision variables
    x = model.addVars(valid_pairs, vtype=GRB.BINARY, name="x")

    # Objective: maximize total assignments
    model.setObjective(
        gp.quicksum(assignment_value * x[i, j] for (i, j) in valid_pairs),
        GRB.MAXIMIZE
    )

    # Each participant assigned to at most one car
    for i in participants:
        pairs_for_participant = [(pi, pj) for (pi, pj) in valid_pairs if pi == i]
        if pairs_for_participant:
            model.addConstr(
                gp.quicksum(x[i, j] for (i, j) in pairs_for_participant) <= 1,
                name=f"participant_{i}"
            )

    # Each car assigned to at most one participant
    for j in cars:
        pairs_for_car = [(pi, pj) for (pi, pj) in valid_pairs if pj == j]
        if pairs_for_car:
            model.addConstr(
                gp.quicksum(x[i, j] for (i, j) in pairs_for_car) <= 1,
                name=f"car_{j}"
            )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}