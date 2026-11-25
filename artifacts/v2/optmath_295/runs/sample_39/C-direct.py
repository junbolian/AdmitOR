import gurobipy as gp
from gurobipy import GRB

def solve(params):
    package_weights = params["package_weights"]
    truck_capacity = params["truck_capacity"]
    num_available_trucks = params["num_available_trucks"]

    num_packages = len(package_weights)
    num_trucks = num_available_trucks

    packages = range(num_packages)
    trucks = range(num_trucks)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i][j] = 1 if package i is assigned to truck j
    x = [[model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}") for j in trucks] for i in packages]

    # y[j] = 1 if truck j is used
    y = [model.addVar(vtype=GRB.BINARY, name=f"y_{j}") for j in trucks]

    # Objective: minimize number of trucks used
    model.setObjective(gp.quicksum(y[j] for j in trucks), GRB.MINIMIZE)

    # Each package assigned to exactly one truck
    for i in packages:
        model.addConstr(gp.quicksum(x[i][j] for j in trucks) == 1, name=f"assign_{i}")

    # Capacity constraints
    for j in trucks:
        model.addConstr(
            gp.quicksum(package_weights[i] * x[i][j] for i in packages) <= truck_capacity * y[j],
            name=f"capacity_{j}"
        )

    # Link x to y: if any package is on truck j, y[j] must be 1
    for j in trucks:
        for i in packages:
            model.addConstr(x[i][j] <= y[j], name=f"link_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}