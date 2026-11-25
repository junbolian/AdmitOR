import gurobipy as gp
from gurobipy import GRB

def solve(params):
    preferences = params["participant_preferences"]
    max_per_participant = params["max_assignments_per_participant"]
    max_per_car = params["max_participants_per_car"]
    obj_coeffs = params["objective_coefficients"]

    num_participants = len(preferences)
    num_cars = len(preferences[0])

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary decision variables
    x = {}
    for i in range(num_participants):
        for j in range(num_cars):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Objective: maximize weighted assignments
    model.setObjective(
        gp.quicksum(obj_coeffs[i][j] * x[i, j]
                    for i in range(num_participants)
                    for j in range(num_cars)),
        GRB.MAXIMIZE
    )

    # Preference constraints: can only assign if interested
    for i in range(num_participants):
        for j in range(num_cars):
            if preferences[i][j] == 0:
                model.addConstr(x[i, j] == 0, name=f"pref_{i}_{j}")

    # Each participant assigned to at most max_per_participant cars
    for i in range(num_participants):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_cars)) <= max_per_participant[i],
            name=f"cap_participant_{i}"
        )

    # Each car assigned to at most max_per_car participants
    for j in range(num_cars):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_participants)) <= max_per_car[j],
            name=f"cap_car_{j}"
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
        return {"objective": None, "status": f"status_{status}"}