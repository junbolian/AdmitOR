import gurobipy as gp
from gurobipy import GRB

def solve(params):
    assignment_value = params["assignment_value"]
    preference_p0_c5 = params["preference_p0_c5"]
    preference_p1_c2 = params["preference_p1_c2"]
    preference_p1_c3 = params["preference_p1_c3"]
    preference_p2_c4 = params["preference_p2_c4"]
    preference_p3_any = params["preference_p3_any"]
    preference_p4_any = params["preference_p4_any"]
    preference_p5_any = params["preference_p5_any"]
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]

    # Build preference matrix from params
    # Rows: participants 0..5, Cols: cars 0..5
    pref = {}
    for p in range(num_participants):
        for c in range(num_cars):
            pref[(p, c)] = 0.0

    pref[(0, 5)] = preference_p0_c5
    pref[(1, 2)] = preference_p1_c2
    pref[(1, 3)] = preference_p1_c3
    pref[(2, 4)] = preference_p2_c4
    # participants 3, 4, 5 have zero interest in all cars
    # preference_p3_any, preference_p4_any, preference_p5_any are scalars
    # representing their uniform interest; apply to all cars for those participants
    for c in range(num_cars):
        pref[(3, c)] = preference_p3_any
        pref[(4, c)] = preference_p4_any
        pref[(5, c)] = preference_p5_any

    # Only create variables for allowed assignments (pref > 0)
    valid_pairs = [(p, c) for p in range(num_participants)
                          for c in range(num_cars)
                          if pref[(p, c)] > 0]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary assignment variables only for valid pairs
    x = model.addVars(valid_pairs, vtype=GRB.BINARY, name="x")

    # Objective: maximize total assignments weighted by assignment_value
    model.setObjective(
        gp.quicksum(assignment_value * x[p, c] for (p, c) in valid_pairs),
        GRB.MAXIMIZE
    )

    # Each participant assigned to at most one car
    for p in range(num_participants):
        pairs_p = [(p2, c) for (p2, c) in valid_pairs if p2 == p]
        if pairs_p:
            model.addConstr(gp.quicksum(x[p2, c] for (p2, c) in pairs_p) <= 1,
                            name=f"participant_{p}")

    # Each car assigned to at most one participant
    for c in range(num_cars):
        pairs_c = [(p, c2) for (p, c2) in valid_pairs if c2 == c]
        if pairs_c:
            model.addConstr(gp.quicksum(x[p, c2] for (p, c2) in pairs_c) <= 1,
                            name=f"car_{c}")

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