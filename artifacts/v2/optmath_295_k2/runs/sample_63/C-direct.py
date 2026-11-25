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
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]

    num_participants = 4
    num_cars = 4

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = {}
    for p in range(num_participants):
        for c in range(num_cars):
            x[p, c] = model.addVar(vtype=GRB.BINARY, name=f"x_{p}_{c}")

    model.update()

    # obj_coeffs may be a flat list of length 16 or a 2D list; handle both
    def get_coeff(p, c):
        coeff = obj_coeffs[p]
        if isinstance(coeff, (list, tuple)):
            return coeff[c]
        # flat list
        return obj_coeffs[p * num_cars + c]

    model.setObjective(
        gp.quicksum(get_coeff(p, c) * x[p, c]
                    for p in range(num_participants)
                    for c in range(num_cars)),
        GRB.MAXIMIZE
    )

    for p in range(num_participants):
        for c in range(num_cars):
            model.addConstr(x[p, c] <= interest[p][c], name=f"interest_{p}_{c}")

    for p in range(num_participants):
        model.addConstr(
            gp.quicksum(x[p, c] for c in range(num_cars)) <= participant_capacity,
            name=f"participant_cap_{p}"
        )

    for c in range(num_cars):
        model.addConstr(
            gp.quicksum(x[p, c] for p in range(num_participants)) <= car_capacity,
            name=f"car_cap_{c}"
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
        return {"objective": None, "status": f"gurobi_status_{status}"}