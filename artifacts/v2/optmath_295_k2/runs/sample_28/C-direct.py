import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Preference structure (structural/index constants, hardcoded per problem statement)
    preferences = {
        0: [2],
        1: [0],
        2: [0, 1],
        3: [1],
        4: [1],
        5: [],
        6: [3],
    }
    participants = list(preferences.keys())
    cars = list(range(6))

    # Valid (participant, car) pairs
    valid_pairs = [(p, c) for p in participants for c in preferences[p]]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary assignment variables
    x = model.addVars(valid_pairs, vtype=GRB.BINARY, name="x")

    # Maximize total assignments
    model.setObjective(gp.quicksum(x[p, c] for p, c in valid_pairs), GRB.MAXIMIZE)

    # Each participant assigned to at most one car
    for p in participants:
        pairs_for_p = [(p, c) for c in preferences[p]]
        if pairs_for_p:
            model.addConstr(gp.quicksum(x[p, c] for _, c in pairs_for_p) <= 1, name=f"participant_{p}")

    # Each car assigned to at most one participant
    for c in cars:
        pairs_for_c = [(p, c) for p in participants if (p, c) in set(valid_pairs)]
        if pairs_for_c:
            model.addConstr(gp.quicksum(x[p, c] for p, _ in pairs_for_c) <= 1, name=f"car_{c}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}