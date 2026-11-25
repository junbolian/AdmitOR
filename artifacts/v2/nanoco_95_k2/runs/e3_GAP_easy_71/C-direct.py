import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity = params["capacity"]        # list of 3 values
    resource_usage = params["resource_usage"]  # 3x7 matrix
    cost = params["cost"]                # 3x7 matrix

    num_vms = 3
    num_tasks = 7
    vms = range(num_vms)
    tasks = range(num_tasks)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if task j is assigned to VM i
    x = model.addVars(vms, tasks, vtype=GRB.BINARY, name="x")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in vms for j in tasks),
        GRB.MINIMIZE
    )

    # Each task assigned to exactly one VM
    for j in tasks:
        model.addConstr(gp.quicksum(x[i, j] for i in vms) == 1, name=f"task_{j}")

    # Capacity constraints
    for i in vms:
        model.addConstr(
            gp.quicksum(resource_usage[i][j] * x[i, j] for j in tasks) <= capacity[i],
            name=f"cap_{i}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}