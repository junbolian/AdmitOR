import gurobipy as gp
from gurobipy import GRB


def solve(params):
    num_participants = int(params["num_participants"])
    num_cars = int(params["num_cars"])

    preference = {}
    for i in range(num_participants):
        for j in range(num_cars):
            preference[i, j] = params[f"preference_{i}_{j}"]

    model = gp.Model("car_sharing")
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_participants, num_cars, vtype=GRB.BINARY, name="x")

    model.setObjective(gp.quicksum(x[i, j] for i in range(num_participants) for j in range(num_cars)), GRB.MAXIMIZE)

    # Each participant assigned to at most one car
    for i in range(num_participants):
        model.addConstr(gp.quicksum(x[i, j] for j in range(num_cars)) <= 1, name=f"participant_{i}")

    # Each car assigned to at most one participant
    for j in range(num_cars):
        model.addConstr(gp.quicksum(x[i, j] for i in range(num_participants)) <= 1, name=f"car_{j}")

    # Respect preferences
    for i in range(num_participants):
        for j in range(num_cars):
            if preference[i, j] == 0:
                model.addConstr(x[i, j] == 0, name=f"pref_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}