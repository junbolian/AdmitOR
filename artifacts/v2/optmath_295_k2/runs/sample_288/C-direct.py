import gurobipy as gp
from gurobipy import GRB

def solve(params):
    resource_weights = params["resource_weights"]  # list of 6 weights
    center_capacity = params["center_capacity"]    # uniform capacity (scalar)

    n_resources = len(resource_weights)
    # Upper bound on centers needed: worst case each resource gets its own center
    n_centers = n_resources

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # y[j] = 1 if center j is used
    y = model.addVars(n_centers, vtype=GRB.BINARY, name="y")
    # x[i,j] = 1 if resource i is assigned to center j
    x = model.addVars(n_resources, n_centers, vtype=GRB.BINARY, name="x")

    # Minimize number of centers used
    model.setObjective(gp.quicksum(y[j] for j in range(n_centers)), GRB.MINIMIZE)

    # Each resource must be assigned to exactly one center
    for i in range(n_resources):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n_centers)) == 1, name=f"assign_{i}")

    # Capacity constraint for each center
    for j in range(n_centers):
        model.addConstr(
            gp.quicksum(resource_weights[i] * x[i, j] for i in range(n_resources)) <= center_capacity * y[j],
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