import gurobipy as gp
from gurobipy import GRB


def solve(params):
    # params is the preferences dict itself: keys are participant indices (int or str),
    # values are lists of acceptable car indices.
    # Handle both cases: params may be the adjacency list directly, or contain it under "preferences".
    if "preferences" in params:
        preferences = params["preferences"]
    else:
        preferences = params

    num_participants = 7
    num_cars = 7

    # Build the set of valid (participant, car) pairs from preferences
    valid_pairs = []
    for p in range(num_participants):
        cars = preferences.get(p, preferences.get(str(p), []))
        for c in cars:
            valid_pairs.append((p, c))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary assignment variables only for valid (participant, car) pairs
    x = model.addVars(valid_pairs, vtype=GRB.BINARY, name="x")

    # Maximize total assignments
    model.setObjective(gp.quicksum(x[p, c] for p, c in valid_pairs), GRB.MAXIMIZE)

    # Each participant assigned to at most one car
    for p in range(num_participants):
        p_pairs = [(pp, c) for (pp, c) in valid_pairs if pp == p]
        if p_pairs:
            model.addConstr(
                gp.quicksum(x[pp, c] for (pp, c) in p_pairs) <= 1,
                name=f"one_car_per_participant_{p}"
            )

    # Each car assigned to at most one participant
    for c in range(num_cars):
        c_pairs = [(p, cc) for (p, cc) in valid_pairs if cc == c]
        if c_pairs:
            model.addConstr(
                gp.quicksum(x[p, cc] for (p, cc) in c_pairs) <= 1,
                name=f"one_participant_per_car_{c}"
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