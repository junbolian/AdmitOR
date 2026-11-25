import gurobipy as gp
from gurobipy import GRB

def solve(params):
    pref = params["preference_matrix"]
    unit_value = params["unit_assignment_value"]

    n_participants = len(pref)
    n_cars = len(pref[0])

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary assignment variables only where participant is eligible
    x = {}
    for p in range(n_participants):
        for c in range(n_cars):
            if pref[p][c] == 1:
                x[p, c] = model.addVar(vtype=GRB.BINARY, name=f"x_{p}_{c}")

    model.update()

    # Objective: maximize total assignments
    model.setObjective(
        gp.quicksum(unit_value * x[p, c] for (p, c) in x),
        GRB.MAXIMIZE
    )

    # Each participant assigned to at most one car
    for p in range(n_participants):
        eligible = [x[p, c] for c in range(n_cars) if (p, c) in x]
        if eligible:
            model.addConstr(gp.quicksum(eligible) <= 1, name=f"participant_{p}")

    # Each car assigned to at most one participant
    for c in range(n_cars):
        eligible = [x[p, c] for p in range(n_participants) if (p, c) in x]
        if eligible:
            model.addConstr(gp.quicksum(eligible) <= 1, name=f"car_{c}")

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