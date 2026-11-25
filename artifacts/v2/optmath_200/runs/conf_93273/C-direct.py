import gurobipy as gp
from gurobipy import GRB

def solve(params):
    assignment_value = params["assignment_value"]

    # Define eligibility from params
    eligibility = {
        (0, 0): params["participant_0_pref_car_0"],
        (0, 5): params["participant_0_pref_car_5"],
        (0, 6): params["participant_0_pref_car_6"],
        (2, 1): params["participant_2_pref_car_1"],
        (2, 3): params["participant_2_pref_car_3"],
        (2, 6): params["participant_2_pref_car_6"],
        (3, 1): params["participant_3_pref_car_1"],
        (3, 5): params["participant_3_pref_car_5"],
        (3, 6): params["participant_3_pref_car_6"],
        (4, 3): params["participant_4_pref_car_3"],
        (5, 0): params["participant_5_pref_car_0"],
        (5, 6): params["participant_5_pref_car_6"],
        (6, 0): params["participant_6_pref_car_0"],
    }

    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]

    num_participants = 7
    num_cars = 7

    participants = range(num_participants)
    cars = range(num_cars)

    # Feasible (participant, car) pairs where eligibility > 0
    feasible_pairs = [(p, c) for (p, c), val in eligibility.items() if val > 0]

    model = gp.Model("car_assignment")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[p, c] = 1 if participant p is assigned to car c
    x = model.addVars(feasible_pairs, vtype=GRB.BINARY, name="x")

    # Objective: maximize total assignments
    model.setObjective(
        gp.quicksum(assignment_value * x[p, c] for (p, c) in feasible_pairs),
        GRB.MAXIMIZE
    )

    # Each participant assigned to at most participant_capacity cars
    for p in participants:
        pairs_for_p = [(p2, c) for (p2, c) in feasible_pairs if p2 == p]
        if pairs_for_p:
            model.addConstr(
                gp.quicksum(x[p2, c] for (p2, c) in pairs_for_p) <= participant_capacity,
                name=f"participant_cap_{p}"
            )

    # Each car assigned to at most car_capacity participants
    for c in cars:
        pairs_for_c = [(p, c2) for (p, c2) in feasible_pairs if c2 == c]
        if pairs_for_c:
            model.addConstr(
                gp.quicksum(x[p, c2] for (p, c2) in pairs_for_c) <= car_capacity,
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