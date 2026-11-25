import gurobipy as gp
from gurobipy import GRB

def solve(params):
    max_per_participant = params["max_assignments_per_participant"]
    max_per_car = params["max_assignments_per_car"]

    num_participants = 6
    num_cars = 6

    preferences = {
        0: [0, 2, 4],
        1: [3],
        2: [0, 1, 3],
        3: [0, 1, 2],
        4: [3, 5],
        5: [1, 2, 3],
    }

    valid_pairs = [
        (p, c)
        for p in range(num_participants)
        for c in preferences[p]
    ]

    model = gp.Model("car_sharing")
    model.setParam("OutputFlag", 0)

    x = model.addVars(valid_pairs, vtype=GRB.BINARY, name="x")

    model.setObjective(gp.quicksum(x[p, c] for p, c in valid_pairs), GRB.MAXIMIZE)

    for p in range(num_participants):
        pairs_for_p = [(p2, c) for p2, c in valid_pairs if p2 == p]
        if pairs_for_p:
            model.addConstr(
                gp.quicksum(x[p2, c] for p2, c in pairs_for_p) <= max_per_participant,
                name=f"participant_{p}"
            )

    for c in range(num_cars):
        pairs_for_c = [(p, c2) for p, c2 in valid_pairs if c2 == c]
        if pairs_for_c:
            model.addConstr(
                gp.quicksum(x[p, c2] for p, c2 in pairs_for_c) <= max_per_car,
                name=f"car_{c}"
            )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}