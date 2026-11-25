import gurobipy as gp
from gurobipy import GRB

def solve(params):
    preference_matrix = params["preference_matrix"]
    cap_participant = params["assignment_capacity_per_participant"]
    cap_car = params["assignment_capacity_per_car"]
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]
    weight = params["objective_weight_per_assignment"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    participants = range(num_participants)
    cars = range(num_cars)

    # Binary assignment variables only where preference allows
    x = {}
    for i in participants:
        for j in cars:
            if preference_matrix[i][j] == 1:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Each participant assigned to at most cap_participant cars
    for i in participants:
        assigned = [x[i, j] for j in cars if (i, j) in x]
        if assigned:
            model.addConstr(gp.quicksum(assigned) <= cap_participant)

    # Each car assigned to at most cap_car participants
    for j in cars:
        assigned = [x[i, j] for i in participants if (i, j) in x]
        if assigned:
            model.addConstr(gp.quicksum(assigned) <= cap_car)

    # Maximize total weighted assignments
    model.setObjective(
        weight * gp.quicksum(x[i, j] for (i, j) in x),
        GRB.MAXIMIZE
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