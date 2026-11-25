import gurobipy as gp
from gurobipy import GRB

def solve(params):
    interest = [
        params["participant_car_interest_p0"],
        params["participant_car_interest_p1"],
        params["participant_car_interest_p2"],
        params["participant_car_interest_p3"],
    ]
    obj_coeffs = params["assignment_objective_coefficients"]
    participant_cap = params["participant_capacity"]
    car_cap = params["car_capacity"]

    num_participants = 4
    num_cars = 4

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = [
        [model.addVar(vtype=GRB.BINARY, name=f"x_{p}_{c}") for c in range(num_cars)]
        for p in range(num_participants)
    ]

    model.setObjective(
        gp.quicksum(obj_coeffs[c] * x[p][c]
                    for p in range(num_participants)
                    for c in range(num_cars)),
        GRB.MAXIMIZE
    )

    for p in range(num_participants):
        for c in range(num_cars):
            model.addConstr(x[p][c] <= interest[p][c], name=f"interest_{p}_{c}")

    for p in range(num_participants):
        cap_p = participant_cap[p] if isinstance(participant_cap, (list, tuple)) else participant_cap
        model.addConstr(
            gp.quicksum(x[p][c] for c in range(num_cars)) <= cap_p,
            name=f"participant_cap_{p}"
        )

    for c in range(num_cars):
        cap_c = car_cap[c] if isinstance(car_cap, (list, tuple)) else car_cap
        model.addConstr(
            gp.quicksum(x[p][c] for p in range(num_participants)) <= cap_c,
            name=f"car_cap_{c}"
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