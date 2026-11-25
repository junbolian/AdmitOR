import gurobipy as gp
from gurobipy import GRB

def solve(params):
    weights = params["package_weights"]
    capacity = params["truck_capacity"]
    num_trucks = params["num_trucks"]

    num_packages = len(weights)
    packages = range(num_packages)
    trucks = range(num_trucks)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i][j] = 1 if package i is assigned to truck j
    x = [[model.addVar(vtype=GRB.BINARY) for j in trucks] for i in packages]
    # y[j] = 1 if truck j is used
    y = [model.addVar(vtype=GRB.BINARY) for j in trucks]

    # Objective: minimize number of trucks used
    model.setObjective(gp.quicksum(y[j] for j in trucks), GRB.MINIMIZE)

    # Each package assigned to exactly one truck
    for i in packages:
        model.addConstr(gp.quicksum(x[i][j] for j in trucks) == 1)

    # Capacity constraints
    for j in trucks:
        model.addConstr(
            gp.quicksum(weights[i] * x[i][j] for i in packages) <= capacity * y[j]
        )

    # Link x to y: if any package is on truck j, truck j is used
    # (the capacity constraint already forces y[j]=1 if any x[i][j]=1 and weights>0;
    #  add explicit linking to be safe with zero-weight edge cases)
    for j in trucks:
        for i in packages:
            model.addConstr(x[i][j] <= y[j])

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}