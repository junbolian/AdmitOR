import gurobipy as gp
from gurobipy import GRB


def solve(params):
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]
    preferences = params["preferences"]

    participants = range(num_participants)
    cars = range(num_cars)

    # Build the set of valid (participant, car) pairs
    valid_pairs = [
        (i, j)
        for i in participants
        for j in preferences[i]
        if j < num_cars
    ]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary assignment variables only for valid pairs
    x = model.addVars(valid_pairs, vtype=GRB.BINARY, name="x")

    # Maximize total assignments
    model.setObjective(gp.quicksum(x[i, j] for (i, j) in valid_pairs), GRB.MAXIMIZE)

    # Each participant assigned to at most one car
    for i in participants:
        pairs_for_i = [(i, j) for (pi, j) in valid_pairs if (pi == i) for _ in [None]]
        # cleaner comprehension:
        pairs_for_i = [j for (pi, j) in valid_pairs if pi == i]
        if pairs_for_i:
            model.addConstr(
                gp.quicksum(x[i, j] for j in pairs_for_i) <= 1,
                name=f"one_car_per_participant_{i}"
            )

    # Each car assigned to at most one participant
    for j in cars:
        pairs_for_j = [i for (i, cj) in valid_pairs if cj == j]
        if pairs_for_j:
            model.addConstr(
                gp.quicksum(x[i, j] for i in pairs_for_j) <= 1,
                name=f"one_participant_per_car_{j}"
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