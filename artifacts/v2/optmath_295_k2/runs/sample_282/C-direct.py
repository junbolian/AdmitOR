import gurobipy as gp
from gurobipy import GRB

def solve(params):
    participant_count = params["participant_count"]
    car_count = params["car_count"]

    # Build preference matrix from params
    preference = {}
    for p in range(participant_count):
        for c in range(car_count):
            preference[(p, c)] = params[f"preference_p{p}_car{c}"]

    model = gp.Model("car_sharing")
    model.setParam("OutputFlag", 0)

    # Binary assignment variables: x[p,c] = 1 if participant p assigned to car c
    x = model.addVars(participant_count, car_count, vtype=GRB.BINARY, name="x")

    # Objective: maximize total assignments
    model.setObjective(
        gp.quicksum(x[p, c] for p in range(participant_count) for c in range(car_count)),
        GRB.MAXIMIZE
    )

    # Each participant assigned to at most one car
    for p in range(participant_count):
        model.addConstr(
            gp.quicksum(x[p, c] for c in range(car_count)) <= 1,
            name=f"one_car_per_participant_{p}"
        )

    # Each car assigned to at most one participant
    for c in range(car_count):
        model.addConstr(
            gp.quicksum(x[p, c] for p in range(participant_count)) <= 1,
            name=f"one_participant_per_car_{c}"
        )

    # Only assign if participant prefers that car
    for p in range(participant_count):
        for c in range(car_count):
            if preference[(p, c)] == 0:
                model.addConstr(x[p, c] == 0, name=f"pref_{p}_{c}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}