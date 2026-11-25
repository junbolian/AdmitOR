import gurobipy as gp
from gurobipy import GRB

def solve(params):
    participant_count = params["participant_count"]
    car_count = params["car_count"]
    preference = params["preference"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    assignment_value = params["assignment_value"]

    participants = range(participant_count)
    cars = range(car_count)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = {}
    for i in participants:
        for j in cars:
            if preference[i][j] == 1:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    val = float(assignment_value)

    model.setObjective(
        gp.quicksum(val * x[i, j] for (i, j) in x),
        GRB.MAXIMIZE
    )

    for i in participants:
        assigned = [x[i, j] for j in cars if (i, j) in x]
        if assigned:
            model.addConstr(
                gp.quicksum(assigned) <= float(participant_capacity[i]),
                name=f"participant_cap_{i}"
            )

    for j in cars:
        assigned = [x[i, j] for i in participants if (i, j) in x]
        if assigned:
            model.addConstr(
                gp.quicksum(assigned) <= float(car_capacity[j]),
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