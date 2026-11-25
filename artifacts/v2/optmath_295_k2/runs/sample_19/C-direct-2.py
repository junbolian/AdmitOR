import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]

    preferences = {
        0: params["preference_p0"],
        1: params["preference_p1"],
        2: params["preference_p2"],
        3: params["preference_p3"],
        4: params["preference_p4"],
        5: params["preference_p5"],
        6: params["preference_p6"],
        7: params["preference_p7"],
    }

    participants = range(num_participants)
    cars = range(num_cars)

    # Build the set of valid (participant, car) pairs
    valid_pairs = [
        (p, c)
        for p in participants
        for c in preferences[p]
    ]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary assignment variables only for valid pairs
    x = model.addVars(valid_pairs, vtype=GRB.BINARY, name="x")

    # Objective: maximize total assignments
    model.setObjective(gp.quicksum(x[p, c] for p, c in valid_pairs), GRB.MAXIMIZE)

    # Each participant assigned to at most one car
    for p in participants:
        pairs_for_p = [(p, c) for c in preferences[p]]
        if pairs_for_p:
            model.addConstr(
                gp.quicksum(x[p, c] for _, c in pairs_for_p) <= 1,
                name=f"participant_{p}"
            )

    # Each car assigned to at most one participant
    for c in cars:
        pairs_for_c = [(p, c) for p in participants if (p, c) in x]
        if pairs_for_c:
            model.addConstr(
                gp.quicksum(x[p, c] for p, _ in pairs_for_c) <= 1,
                name=f"car_{c}"
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