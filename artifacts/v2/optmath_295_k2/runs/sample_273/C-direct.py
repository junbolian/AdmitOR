import gurobipy as gp
from gurobipy import GRB

def solve(params):
    preference = params["preference"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    assignment_value = params["assignment_value"]

    num_participants = 8
    num_cars = 8

    model = gp.Model("car_sharing")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i][j] = 1 if participant i is assigned to car j
    x = {}
    for i in range(num_participants):
        for j in range(num_cars):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Objective: maximize total assignment value
    model.setObjective(
        gp.quicksum(assignment_value * preference[i][j] * x[i, j]
                    for i in range(num_participants)
                    for j in range(num_cars)),
        GRB.MAXIMIZE
    )

    # Preference constraint: can only assign if interested
    for i in range(num_participants):
        for j in range(num_cars):
            if preference[i][j] == 0:
                model.addConstr(x[i, j] == 0, name=f"pref_{i}_{j}")

    # Participant capacity constraint
    for i in range(num_participants):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_cars)) <= participant_capacity[i],
            name=f"part_cap_{i}"
        )

    # Car capacity constraint
    for j in range(num_cars):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_participants)) <= car_capacity[j],
            name=f"car_cap_{j}"
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