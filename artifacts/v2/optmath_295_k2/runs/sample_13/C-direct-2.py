import gurobipy as gp
from gurobipy import GRB


def solve(params):
    preference_matrix = params["preference_matrix"]
    cap_participant = params["assignment_cap_per_participant"]
    cap_car = params["assignment_cap_per_car"]

    num_participants = len(preference_matrix)
    num_cars = len(preference_matrix[0])

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i][j] = 1 if participant i is assigned to car j
    x = {
        (i, j): model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")
        for i in range(num_participants)
        for j in range(num_cars)
        if preference_matrix[i][j] == 1
    }

    # Maximize total assignments
    model.setObjective(gp.quicksum(x.values()), GRB.MAXIMIZE)

    # Each participant assigned to at most cap_participant cars
    for i in range(num_participants):
        assigned = [x[(i, j)] for j in range(num_cars) if (i, j) in x]
        if assigned:
            model.addConstr(gp.quicksum(assigned) <= cap_participant, name=f"cap_p_{i}")

    # Each car assigned to at most cap_car participants
    for j in range(num_cars):
        assigned = [x[(i, j)] for i in range(num_participants) if (i, j) in x]
        if assigned:
            model.addConstr(gp.quicksum(assigned) <= cap_car, name=f"cap_c_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}