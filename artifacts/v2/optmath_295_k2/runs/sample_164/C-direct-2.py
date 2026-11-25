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

    # assignment_value may be a scalar weight or a participant x car matrix.
    av_is_scalar = isinstance(assignment_value, (int, float))

    def coeff(i, j):
        if av_is_scalar:
            return assignment_value
        return assignment_value[i][j]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i,j] = 1 if participant i is assigned to car j
    x = {}
    for i in participants:
        for j in cars:
            if preference[i][j] == 1:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Objective: maximize total weighted assignments
    model.setObjective(
        gp.quicksum(coeff(i, j) * x[i, j] for (i, j) in x),
        GRB.MAXIMIZE
    )

    # Each participant assigned to at most participant_capacity[i] cars
    for i in participants:
        assigned = [x[i, j] for j in cars if (i, j) in x]
        if assigned:
            model.addConstr(
                gp.quicksum(assigned) <= participant_capacity[i],
                name=f"participant_cap_{i}"
            )

    # Each car assigned to at most car_capacity[j] participants
    for j in cars:
        assigned = [x[i, j] for i in participants if (i, j) in x]
        if assigned:
            model.addConstr(
                gp.quicksum(assigned) <= car_capacity[j],
                name=f"car_cap_{j}"
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