import gurobipy as gp
from gurobipy import GRB

def solve(params):
    participants = ["participant_0", "participant_1", "participant_2", "participant_3"]
    cars = ["car_0", "car_1", "car_2", "car_3", "car_4"]

    preferences = {
        "participant_0": {"car_2": 1, "car_4": 1},
        "participant_1": {},
        "participant_2": {"car_0": 1, "car_4": 1},
        "participant_3": {"car_0": 1, "car_4": 1},
    }

    allowed = [
        (p, c)
        for p in participants
        for c in cars
        if preferences[p].get(c, 0) == 1
    ]

    model = gp.Model("carpooling")
    model.setParam("OutputFlag", 0)

    x = model.addVars(allowed, vtype=GRB.BINARY, name="x")

    model.setObjective(gp.quicksum(x[p, c] for p, c in allowed), GRB.MAXIMIZE)

    for p in participants:
        pairs = [(p2, c) for p2, c in allowed if p2 == p]
        if pairs:
            model.addConstr(gp.quicksum(x[p2, c] for p2, c in pairs) <= 1, name=f"one_car_{p}")

    for c in cars:
        pairs = [(p, c2) for p, c2 in allowed if c2 == c]
        if pairs:
            model.addConstr(gp.quicksum(x[p, c2] for p, c2 in pairs) <= 1, name=f"one_participant_{c}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}