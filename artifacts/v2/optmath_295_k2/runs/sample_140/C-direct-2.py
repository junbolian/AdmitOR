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
            pref[(p, c)] = 0

    pref[(0, 5)] = preference_p0_c5
    pref[(1, 2)] = preference_p1_c2
    pref[(1, 3)] = preference_p1_c3
    pref[(2, 4)] = preference_p2_c4

    # Participants 3, 4, 5: all zero per params
    # preference_p3_any, preference_p4_any, preference_p5_any represent
    # the uniform interest level; apply to all cars for those participants
    for c in range(num_cars):
        pref[(3, c)] = preference_p3_any
        pref[(4, c)] = preference_p4_any
        pref[(5, c)] = preference_p5_any

    # Only create decision variables for valid (pref == 1) pairs
    valid_pairs = [(p, c) for p in range(num_participants)
                          for c in range(num_cars)
                          if pref[(p, c)] == 1]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(valid_pairs, vtype=GRB.BINARY, name="x")

    # Objective: maximize total assignments weighted by assignment_value
    model.setObjective(
        gp.quicksum(assignment_value * x[p, c] for p, c in valid_pairs),
        GRB.MAXIMIZE
    )

    # Each participant assigned to at most one car
    for p in range(num_participants):
        pairs_p = [(p, c) for (pp, c) in valid_pairs if pp == p]
        if pairs_p:
            model.addConstr(
                gp.quicksum(x[p, c] for _, c in [(pp, cc) for (pp, cc) in valid_pairs if pp == p]) <= 1,
                name=f"participant_{p}"
            )

    # Each car assigned to at most one participant
    for c in range(num_cars):
        pairs_c = [(p, c) for (p, cc) in valid_pairs if cc == c]
        if pairs_c:
            model.addConstr(
                gp.quicksum(x[p, c] for p, _ in [(pp, cc) for (pp, cc) in valid_pairs if cc == c]) <= 1,
                name=f"car_{c}"
            )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}