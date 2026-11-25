import gurobipy as gp
from gurobipy import GRB

def solve(params):
    package_weights = params["package_weights"]
    truck_capacity = params["truck_capacity"]

    n_packages = len(package_weights)
    n_trucks = n_packages  # upper bound: one truck per package

    packages = range(n_packages)
    trucks = range(n_trucks)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i, j] = 1 if package i is assigned to truck j
    x = model.addVars(packages, trucks, vtype=GRB.BINARY, name="x")
    # y[j] = 1 if truck j is used
    y = model.addVars(trucks, vtype=GRB.BINARY, name="y")

    # Objective: minimize number of trucks used
    model.setObjective(gp.quicksum(y[j] for j in trucks), GRB.MINIMIZE)

    # Each package assigned to exactly one truck
    for i in packages:
        model.addConstr(gp.quicksum(x[i, j] for j in trucks) == 1, name=f"assign_{i}")

    # Capacity constraint per truck
    for j in trucks:
        model.addConstr(
            gp.quicksum(package_weights[i] * x[i, j] for i in packages) <= truck_capacity * y[j],
            name=f"capacity_{j}"
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