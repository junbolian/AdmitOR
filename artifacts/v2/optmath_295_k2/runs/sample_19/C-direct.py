import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]

    preferences = {
        0: params["preference_p0"],
        1: params["preference_p1"],
        2: params["preference_p2"],
        3: params["preference_p3"],
        4: params["preference_p4"],
        5: params["preference_p5"],
        6: params["preference_p6"],
        7: params["preference_p7"],
    }

    model = gp.Model("car_assignment")
    model.setParam("OutputFlag", 0)

    # x[p, c] = 1 if participant p is assigned to car c
    x = {}
    for p in range(num_participants):
        for c in preferences[p]:
            x[p, c] = model.addVar(vtype=GRB.BINARY, name=f"x_{p}_{c}")

    # Each participant assigned to at most one car
    for p in range(num_participants):
        cars_for_p = preferences[p]
        if cars_for_p:
            model.addConstr(
                gp.quicksum(x[p, c] for c in cars_for_p) <= 1,
                name=f"participant_{p}"
            )

    # Each car assigned to at most one participant
    for c in range(num_cars):
        participants_for_c = [p for p in range(num_participants) if c in preferences[p]]
        if len(participants_for_c) > 1:
            model.addConstr(
                gp.quicksum(x[p, c] for p in participants_for_c) <= 1,
                name=f"car_{c}"
            )

    # Maximize total assignments
    model.setObjective(
        gp.quicksum(x[p, c] for (p, c) in x),
        GRB.MAXIMIZE
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