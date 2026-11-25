import gurobipy as gp
from gurobipy import GRB

def solve(params):
    obj_coeff = params["objective_coefficient"]

    # Preferences: participant -> list of interested cars
    preferences = {
        0: [1, 6, 7],
        1: [3],
        2: [1, 2, 4],
        3: [0],
        4: [2, 4, 5],
        5: [],
        6: [0, 1, 2, 3, 5],
    }

    # Build the set of valid (participant, car) pairs
    valid_pairs = [
        (p, c)
        for p, cars in preferences.items()
        for c in cars
    ]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary assignment variables for valid pairs only
    x = model.addVars(valid_pairs, vtype=GRB.BINARY, name="x")

    # Objective: maximize total assignments
    model.setObjective(
        gp.quicksum(obj_coeff * x[p, c] for p, c in valid_pairs),
        GRB.MAXIMIZE
    )

    # Each participant assigned to at most one car
    for p in range(7):
        pairs_for_p = [(p2, c) for p2, c in valid_pairs if p2 == p]
        if pairs_for_p:
            model.addConstr(gp.quicksum(x[p2, c] for p2, c in pairs_for_p) <= 1)

    # Each car assigned to at most one participant
    for c in range(8):
        pairs_for_c = [(p, c2) for p, c2 in valid_pairs if c2 == c]
        if pairs_for_c:
            model.addConstr(gp.quicksum(x[p, c2] for p, c2 in pairs_for_c) <= 1)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}