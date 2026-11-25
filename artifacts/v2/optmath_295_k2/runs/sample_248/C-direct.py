import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Read parameters
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]
    capacity_per_participant = params["assignment_capacity_per_participant"]
    capacity_per_car = params["assignment_capacity_per_car"]

    # Build allowed assignments from preference parameters
    preferences = {
        0: params["participant_0_preferred_car_3"],
        1: params["participant_1_preferred_car_1"],
        2: params["participant_2_preferred_cars_1_3"],
        3: params["participant_3_preferred_cars_2_4"],
        4: params["participant_4_preferred_cars_3_5"],
        5: params["participant_5_preferred_cars_2_6"],
        6: params["participant_6_preferred_car_6"],
    }

    # Normalize preferences to lists of car indices
    allowed = {}
    for p in range(num_participants):
        pref = preferences[p]
        if isinstance(pref, (list, tuple)):
            allowed[p] = list(pref)
        else:
            allowed[p] = [int(pref)]

    # Build set of valid (participant, car) pairs
    valid_pairs = [(p, c) for p in range(num_participants) for c in allowed[p] if c < num_cars]

    model = gp.Model("car_assignment")
    model.setParam("OutputFlag", 0)

    # Decision variables
    domain = params["assignment_variable_domain"]
    if domain == 1 or domain == "binary":
        x = model.addVars(valid_pairs, vtype=GRB.BINARY, name="x")
    else:
        x = model.addVars(valid_pairs, vtype=GRB.BINARY, name="x")

    # Objective: maximize total assignments
    model.setObjective(gp.quicksum(x[p, c] for p, c in valid_pairs), GRB.MAXIMIZE)

    # Each participant assigned to at most capacity_per_participant cars
    for p in range(num_participants):
        pairs_p = [(p, c) for c in allowed[p] if c < num_cars]
        if pairs_p:
            model.addConstr(
                gp.quicksum(x[p, c] for _, c in pairs_p) <= capacity_per_participant,
                name=f"cap_participant_{p}"
            )

    # Each car assigned to at most capacity_per_car participants
    for c in range(num_cars):
        pairs_c = [(p, c) for p in range(num_participants) if c in allowed[p] and (p, c) in set(valid_pairs)]
        if pairs_c:
            model.addConstr(
                gp.quicksum(x[p, c] for p, _ in pairs_c) <= capacity_per_car,
                name=f"cap_car_{c}"
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
        return {"objective": None, "status": f"solver_status_{status}"}