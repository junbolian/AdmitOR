import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n_participants = 6
    n_cars = 7

    # Build preference lookup from params
    preferences = {}
    for i in range(n_participants):
        for j in range(n_cars):
            key = f"preference_{i}_{j}"
            if key in params:
                preferences[(i, j)] = params[key]
            else:
                preferences[(i, j)] = 0

    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]

    # Valid assignments based on preferences
    valid_pairs = [(i, j) for i in range(n_participants) for j in range(n_cars)
                   if preferences[(i, j)] == 1]

    model = gp.Model("carpooling")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i,j] = 1 if participant i assigned to car j
    x = model.addVars(valid_pairs, vtype=GRB.BINARY, name="x")

    # Objective: maximize total assignments
    model.setObjective(gp.quicksum(x[i, j] for (i, j) in valid_pairs), GRB.MAXIMIZE)

    # Each participant assigned to at most participant_capacity cars
    for i in range(n_participants):
        pairs_i = [(i, j) for (pi, j) in [p for p in valid_pairs if p[0] == i] for _ in [None]]
        pairs_i = [(i, j) for (i2, j) in valid_pairs if i2 == i]
        if pairs_i:
            model.addConstr(gp.quicksum(x[i, j] for (i2, j) in pairs_i) <= participant_capacity,
                            name=f"participant_{i}_cap")

    # Each car assigned to at most car_capacity participants
    for j in range(n_cars):
        pairs_j = [(i, j2) for (i, j2) in valid_pairs if j2 == j]
        if pairs_j:
            model.addConstr(gp.quicksum(x[i, j] for (i, j2) in pairs_j) <= car_capacity,
                            name=f"car_{j}_cap")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}