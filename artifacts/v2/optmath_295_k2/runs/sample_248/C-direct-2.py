import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Read parameters
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]
    capacity_per_participant = params["assignment_capacity_per_participant"]
    capacity_per_car = params["assignment_capacity_per_car"]

    # Build allowed assignments from preference parameters
    allowed = {
        0: params["participant_0_preferred_car_3"],
        1: params["participant_1_preferred_car_1"],
        2: params["participant_2_preferred_cars_1_3"],
        3: params["participant_3_preferred_cars_2_4"],
        4: params["participant_4_preferred_cars_3_5"],
        5: params["participant_5_preferred_cars_2_6"],
        6: params["participant_6_preferred_car_6"],
    }

    # Normalize to lists of car indices
    preferences = {}
    for p in range(num_participants):
        val = allowed[p]
        if isinstance(val, (int, float)):
            preferences[p] = [int(val)]
        else:
            preferences[p] = [int(c) for c in val]

    # Build set of valid (participant, car) pairs
    valid_pairs = []
    for p in range(num_participants):
        for c in preferences[p]:
            if 0 <= c < num_cars:
                valid_pairs.append((p, c))

    model = gp.Model("car_assignment")
    model.setParam("OutputFlag", 0)

    # Determine variable type from domain parameter
    domain_val = params["assignment_variable_domain"]
    if domain_val == 1 or str(domain_val).lower() in ("binary", "1"):
        vtype = GRB.BINARY
    else:
        vtype = GRB.BINARY  # default to binary per problem description

    # Decision variables
    x = model.addVars(valid_pairs, vtype=vtype, name="x")

    # Objective: maximize total assignments
    model.setObjective(gp.quicksum(x[p, c] for p, c in valid_pairs), GRB.MAXIMIZE)

    # Constraint 1: each participant assigned to at most capacity_per_participant cars
    for p in range(num_participants):
        pairs_for_p = [(p, c) for pp, c in valid_pairs if pp == p]
        if pairs_for_p:
            model.addConstr(
                gp.quicksum(x[p, c] for _, c in [(pp, cc) for pp, cc in valid_pairs if pp == p]) <= capacity_per_participant,
                name=f"cap_participant_{p}"
            )

    # Constraint 2: each car assigned to at most capacity_per_car participants
    for c in range(num_cars):
        pairs_for_c = [(p, c) for p, cc in valid_pairs if cc == c]
        if pairs_for_c:
            model.addConstr(
                gp.quicksum(x[p, c] for p, _ in pairs_for_c) <= capacity_per_car,
                name=f"cap_car_{c}"
            )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}