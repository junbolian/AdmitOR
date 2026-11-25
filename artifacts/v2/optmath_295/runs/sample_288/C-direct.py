import gurobipy as gp
from gurobipy import GRB

def solve(params):
    resource_weights = params["resource_weights"]
    center_capacity = params["center_capacity"]
    num_resources = params["num_resources"]
    num_centers = params["num_centers_available"]

    resources = range(num_resources)
    centers = range(num_centers)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i, j] = 1 if resource i is assigned to center j
    x = model.addVars(num_resources, num_centers, vtype=GRB.BINARY, name="x")
    # y[j] = 1 if center j is used
    y = model.addVars(num_centers, vtype=GRB.BINARY, name="y")

    # Minimize number of centers used
    model.setObjective(gp.quicksum(y[j] for j in centers), GRB.MINIMIZE)

    # Each resource assigned to exactly one center
    for i in resources:
        model.addConstr(gp.quicksum(x[i, j] for j in centers) == 1, name=f"assign_{i}")

    # Capacity constraints
    for j in centers:
        model.addConstr(
            gp.quicksum(resource_weights[i] * x[i, j] for i in resources) <= center_capacity * y[j],
            name=f"cap_{j}"
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