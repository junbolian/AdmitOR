import gurobipy as gp
from gurobipy import GRB

def solve(params):
    preference_matrix = params["preference_matrix"]
    cap_participant = params["assignment_capacity_per_participant"]
    cap_car = params["assignment_capacity_per_car"]
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]
    obj_weight = float(params["objective_weight_per_assignment"])

    model = gp.Model("carpool_assignment")
    model.setParam("OutputFlag", 0)

    x = {}
    for i in range(num_participants):
        for j in range(num_cars):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"assign_{i}_{j}")

    for i in range(num_participants):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_cars)) <= cap_participant,
            name=f"participant_capacity_{i}",
        )

    for j in range(num_cars):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_participants)) <= cap_car,
            name=f"car_capacity_{j}",
        )

    for i in range(num_participants):
        for j in range(num_cars):
            model.addConstr(
                x[i, j] <= preference_matrix[i][j],
                name=f"preference_{i}_{j}",
            )

    model.setObjective(
        obj_weight * gp.quicksum(
            x[i, j]
            for i in range(num_participants)
            for j in range(num_cars)
        ),
        GRB.MAXIMIZE,
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    if model.status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    return {"objective": None, "status": f"status_{model.status}"}