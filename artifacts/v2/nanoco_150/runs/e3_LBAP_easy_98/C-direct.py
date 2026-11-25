import gurobipy as gp
from gurobipy import GRB

def solve(params):
    processing_time = params["processing_time"]
    n = 5

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if machine i is assigned to job j
    x = model.addVars(n, n, vtype=GRB.BINARY, name="x")
    # z = makespan (max processing time)
    z = model.addVar(lb=0, name="z")

    model.setObjective(z, GRB.MINIMIZE)

    # Each machine assigned exactly one job
    for i in range(n):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n)) == 1)

    # Each job assigned to exactly one machine
    for j in range(n):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n)) == 1)

    # z >= processing time of each assigned pair
    for i in range(n):
        for j in range(n):
            model.addConstr(z >= processing_time[i][j] * x[i, j])

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}