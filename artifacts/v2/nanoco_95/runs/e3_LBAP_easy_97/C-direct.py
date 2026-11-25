import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_matrix = params["cost_matrix"]
    num_workers = 5
    num_tasks = 5

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary assignment variables
    x = model.addVars(num_workers, num_tasks, vtype=GRB.BINARY, name="x")

    # Bottleneck variable: maximum latency
    z = model.addVar(lb=0.0, name="z")

    # Minimize the maximum latency
    model.setObjective(z, GRB.MINIMIZE)

    # Each server assigned exactly one feed
    for i in range(num_workers):
        model.addConstr(gp.quicksum(x[i, j] for j in range(num_tasks)) == 1)

    # Each feed assigned to exactly one server
    for j in range(num_tasks):
        model.addConstr(gp.quicksum(x[i, j] for i in range(num_workers)) == 1)

    # z >= latency of every active assignment
    for i in range(num_workers):
        for j in range(num_tasks):
            model.addConstr(z >= cost_matrix[i][j] * x[i, j])

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}