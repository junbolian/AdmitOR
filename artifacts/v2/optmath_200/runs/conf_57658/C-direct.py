import gurobipy as gp
from gurobipy import GRB

def solve(params):
    pref_p0_c0 = params["pref_p0_c0"]
    pref_p0_c1 = params["pref_p0_c1"]
    pref_p1_c4 = params["pref_p1_c4"]
    pref_p2_none = params["pref_p2_none"]
    pref_p3_none = params["pref_p3_none"]
    pref_p4_c0 = params["pref_p4_c0"]
    pref_p4_c2 = params["pref_p4_c2"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]

    # Build preference matrix: preferences[(p, c)] = binary interest value
    preferences = {
        (0, 0): pref_p0_c0,
        (0, 1): pref_p0_c1,
        (1, 4): pref_p1_c4,
        (4, 0): pref_p4_c0,
        (4, 2): pref_p4_c2,
    }

    num_participants = 5
    num_cars = 5

    # Only create assignment variables for (participant, car) pairs with interest == 1
    valid_pairs = [(p, c) for (p, c), val in preferences.items() if val == 1]

    model = gp.Model("car_assignment")
    model.setParam("OutputFlag", 0)

    # Binary assignment variables
    x = {}
    for (p, c) in valid_pairs:
        x[p, c] = model.addVar(vtype=GRB.BINARY, name=f"x_{p}_{c}")

    model.update()

    # Objective: maximize total successful assignments
    model.setObjective(
        gp.quicksum(x[p, c] for (p, c) in valid_pairs),
        GRB.MAXIMIZE
    )

    # Each participant assigned at most participant_capacity cars
    for p in range(num_participants):
        pairs_for_p = [(p2, c) for (p2, c) in valid_pairs if p2 == p]
        if pairs_for_p:
            model.addConstr(
                gp.quicksum(x[p, c] for (p2, c) in pairs_for_p) <= participant_capacity,
                name=f"participant_cap_{p}"
            )

    # Each car assigned to at most car_capacity participants
    for c in range(num_cars):
        pairs_for_c = [(p, c2) for (p, c2) in valid_pairs if c2 == c]
        if pairs_for_c:
            model.addConstr(
                gp.quicksum(x[p, c] for (p, c2) in pairs_for_c) <= car_capacity,
                name=f"car_cap_{c}"
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