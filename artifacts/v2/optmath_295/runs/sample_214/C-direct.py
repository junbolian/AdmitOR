import gurobipy as gp
from gurobipy import GRB

def solve(params):
    participants = range(6)
    cars = range(7)

    # Build preference matrix from params
    pref_keys = {
        (0, 0): "pref_0_0",
        (0, 6): "pref_0_6",
        (1, 5): "pref_1_5",
        (2, 3): "pref_2_3",
        (2, 6): "pref_2_6",
        (3, 3): "pref_3_3",
        (3, 6): "pref_3_6",
        (4, 1): "pref_4_1",
        (4, 2): "pref_4_2",
        (4, 3): "pref_4_3",
        (5, 1): "pref_5_1",
        (5, 2): "pref_5_2",
        (5, 4): "pref_5_4",
        (5, 5): "pref_5_5",
    }

    pref = {}
    for p in participants:
        for c in cars:
            key = (p, c)
            if key in pref_keys:
                pref[key] = params[pref_keys[key]]
            else:
                pref[key] = 0

    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    assignment_value = params["assignment_value"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: x[p, c] = 1 if participant p is assigned to car c
    x = {}
    for p in participants:
        for c in cars:
            x[p, c] = model.addVar(vtype=GRB.BINARY, name=f"x_{p}_{c}")

    model.update()

    # Objective: maximize total assignment value
    model.setObjective(
        gp.quicksum(assignment_value * pref[p, c] * x[p, c] for p in participants for c in cars),
        GRB.MAXIMIZE
    )

    # Each participant assigned to at most participant_capacity cars
    for p in participants:
        model.addConstr(
            gp.quicksum(x[p, c] for c in cars) <= participant_capacity,
            name=f"participant_cap_{p}"
        )

    # Each car assigned to at most car_capacity participants
    for c in cars:
        model.addConstr(
            gp.quicksum(x[p, c] for p in participants) <= car_capacity,
            name=f"car_cap_{c}"
        )

    # Only allow assignments where preference is set (enforce preference via constraint)
    for p in participants:
        for c in cars:
            if pref[p, c] == 0:
                model.addConstr(x[p, c] == 0, name=f"pref_{p}_{c}")

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