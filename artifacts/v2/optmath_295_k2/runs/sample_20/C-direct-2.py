import gurobipy as gp
from gurobipy import GRB


def solve(params):
    # Support params being the preferences dict directly,
    # or a wrapper with a "preferences" key.
    if "preferences" in params:
        preferences = params["preferences"]
    else:
        preferences = params

    # Normalize keys to int in case they come in as strings
    preferences = {int(k): [int(c) for c in v] for k, v in preferences.items()}

    participants = list(preferences.keys())
    all_cars = set()
    for cars_list in preferences.values():
        all_cars.update(cars_list)
    cars = list(all_cars)

    # Build the set of valid (participant, car) pairs
    valid_pairs = [(p, c) for p in participants for c in preferences[p]]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    if not valid_pairs:
        # No possible assignments
        return {"objective": 0.0, "status": "optimal"}

    # Binary assignment variables only for valid pairs
    x = model.addVars(valid_pairs, vtype=GRB.BINARY, name="x")

    # Maximize total assignments
    model.setObjective(gp.quicksum(x[p, c] for p, c in valid_pairs), GRB.MAXIMIZE)

    # Each participant assigned to at most one car
    for p in participants:
        if preferences[p]:
            model.addConstr(
                gp.quicksum(x[p, c] for c in preferences[p]) <= 1,
                name=f"one_car_per_participant_{p}"
            )

    # Each car assigned to at most one participant
    for c in cars:
        participants_for_c = [p for p in participants if c in preferences[p]]
        if participants_for_c:
            model.addConstr(
                gp.quicksum(x[p, c] for p in participants_for_c) <= 1,
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