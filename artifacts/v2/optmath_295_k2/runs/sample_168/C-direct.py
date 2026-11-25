import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]
    participant_0_4_interest = params["participant_0_4_interest"]
    participant_4_car_1_interest = params["participant_4_car_1_interest"]
    participant_4_forbidden_interest = params["participant_4_forbidden_interest"]

    # Build preference matrix: interest[p][c] = 1 if participant p is interested in car c
    # Participants 0-3: no interest in any car (all zeros, scaled by participant_0_4_interest)
    # Participant 4: interested in car_1 only (not car_0, car_2, car_3)
    interest = {}
    for p in range(num_participants - 1):  # participants 0..3
        for c in range(num_cars):
            interest[(p, c)] = participant_0_4_interest

    # Participant 4
    for c in range(num_cars):
        if c == 1:
            interest[(4, c)] = participant_4_car_1_interest
        else:
            interest[(4, c)] = participant_4_forbidden_interest

    model = gp.Model("assignment")
    model.setParam("OutputFlag", 0)

    # Binary assignment variables
    x = {}
    for p in range(num_participants):
        for c in range(num_cars):
            x[(p, c)] = model.addVar(vtype=GRB.BINARY, name=f"x_{p}_{c}")

    model.update()

    # Objective: maximize total assignments
    model.setObjective(
        gp.quicksum(x[(p, c)] for p in range(num_participants) for c in range(num_cars)),
        GRB.MAXIMIZE
    )

    # Each participant assigned to at most one car
    for p in range(num_participants):
        model.addConstr(
            gp.quicksum(x[(p, c)] for c in range(num_cars)) <= 1,
            name=f"one_car_per_participant_{p}"
        )

    # Each car assigned to at most one participant
    for c in range(num_cars):
        model.addConstr(
            gp.quicksum(x[(p, c)] for p in range(num_participants)) <= 1,
            name=f"one_participant_per_car_{c}"
        )

    # Preference constraints: can only assign if interested
    for p in range(num_participants):
        for c in range(num_cars):
            model.addConstr(
                x[(p, c)] <= interest[(p, c)],
                name=f"interest_{p}_{c}"
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