import gurobipy as gp
from gurobipy import GRB

def solve(params):
    preference = params["preference"]
    num_participants = len(preference)
    num_cars = len(preference[0])

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary assignment variables only where participant is interested
    x = {}
    for i in range(num_participants):
        for j in range(num_cars):
            if preference[i][j] == 1:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Each participant assigned to at most one car
    for i in range(num_participants):
        vars_i = [x[i, j] for j in range(num_cars) if (i, j) in x]
        if vars_i:
            model.addConstr(gp.quicksum(vars_i) <= 1, name=f"participant_{i}")

    # Each car assigned to at most one participant
    for j in range(num_cars):
        vars_j = [x[i, j] for i in range(num_participants) if (i, j) in x]
        if vars_j:
            model.addConstr(gp.quicksum(vars_j) <= 1, name=f"car_{j}")

    # Maximize total assignments
    model.setObjective(gp.quicksum(x.values()), GRB.MAXIMIZE)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{status}"}