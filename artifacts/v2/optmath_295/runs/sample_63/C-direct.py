import gurobipy as gp
from gurobipy import GRB

def solve(params):
    preference = params["preference"]
    
    num_participants = len(preference)
    num_cars = len(preference[0])
    
    participants = range(num_participants)
    cars = range(num_cars)
    
    model = gp.Model()
    model.setParam("OutputFlag", 0)
    
    # Binary assignment variables, only where preference allows
    x = {}
    for i in participants:
        for j in cars:
            if preference[i][j] == 1:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")
    
    # Objective: maximize total assignments
    model.setObjective(gp.quicksum(x[i, j] for (i, j) in x), GRB.MAXIMIZE)
    
    # Each participant assigned to at most one car
    for i in participants:
        eligible = [x[i, j] for j in cars if (i, j) in x]
        if eligible:
            model.addConstr(gp.quicksum(eligible) <= 1, name=f"participant_{i}")
    
    # Each car assigned to at most one participant
    for j in cars:
        eligible = [x[i, j] for i in participants if (i, j) in x]
        if eligible:
            model.addConstr(gp.quicksum(eligible) <= 1, name=f"car_{j}")
    
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