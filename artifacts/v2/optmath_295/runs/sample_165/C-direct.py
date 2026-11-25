import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n_participants = 6
    n_cars = 6

    # Build preference matrix from params (default 0 for unspecified pairs)
    pref = {}
    for i in range(n_participants):
        for j in range(n_cars):
            key = f"participant_{i}_pref_car_{j}"
            pref[(i, j)] = int(params.get(key, 0))

    model = gp.Model("carpooling")
    model.setParam("OutputFlag", 0)

    # Binary assignment variables only for preferred (i, j) pairs
    x = {}
    for i in range(n_participants):
        for j in range(n_cars):
            if pref[(i, j)] == 1:
                x[(i, j)] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    model.update()

    # Each participant assigned to at most one car
    for i in range(n_participants):
        eligible = [x[(i, j)] for j in range(n_cars) if (i, j) in x]
        if eligible:
            model.addConstr(gp.quicksum(eligible) <= 1, name=f"one_car_per_participant_{i}")

    # Each car assigned to at most one participant
    for j in range(n_cars):
        eligible = [x[(i, j)] for i in range(n_participants) if (i, j) in x]
        if eligible:
            model.addConstr(gp.quicksum(eligible) <= 1, name=f"one_participant_per_car_{j}")

    # Maximize total assignments
    model.setObjective(gp.quicksum(x.values()), GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}