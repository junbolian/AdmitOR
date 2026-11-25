import gurobipy as gp
from gurobipy import GRB

def solve(params):
    preferences = {
        0: params["preference_p0"],
        1: params["preference_p1"],
        2: params["preference_p2"],
        3: params["preference_p3"],
        4: params["preference_p4"],
    }
    weight = params["objective_weight_per_assignment"]
    participant_caps = {
        0: params["participant_0_capacity"],
        1: params["participant_1_capacity"],
        2: params["participant_2_capacity"],
        3: params["participant_3_capacity"],
        4: params["participant_4_capacity"],
    }
    car_caps = {
        0: params["car_0_capacity"],
        1: params["car_1_capacity"],
        2: params["car_2_capacity"],
        3: params["car_3_capacity"],
        4: params["car_4_capacity"],
    }

    participants = range(5)
    cars = range(5)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: x[p, c] = 1 if participant p is assigned to car c
    x = {}
    for p in participants:
        for c in cars:
            x[p, c] = model.addVar(vtype=GRB.BINARY, name=f"x_{p}_{c}")

    # Objective: maximize weighted assignments
    model.setObjective(
        weight * gp.quicksum(x[p, c] for p in participants for c in cars),
        GRB.MAXIMIZE
    )

    # Preference constraints: only assign if interested
    for p in participants:
        pref = preferences[p]
        for c in cars:
            if pref[c] == 0:
                model.addConstr(x[p, c] == 0, name=f"pref_{p}_{c}")

    # Participant capacity constraints
    for p in participants:
        model.addConstr(
            gp.quicksum(x[p, c] for c in cars) <= participant_caps[p],
            name=f"pcap_{p}"
        )

    # Car capacity constraints
    for c in cars:
        model.addConstr(
            gp.quicksum(x[p, c] for p in participants) <= car_caps[c],
            name=f"ccap_{c}"
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