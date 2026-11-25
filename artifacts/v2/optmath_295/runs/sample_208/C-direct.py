import gurobipy as gp
from gurobipy import GRB

def solve(params):
    resource_weights = params["resource_weights"]
    facility_capacity = params["facility_capacity"]

    num_resources = len(resource_weights)
    num_facilities = len(resource_weights)  # seven facilities

    resources = range(num_resources)
    facilities = range(num_facilities)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # y[j] = 1 if facility j is used
    y = model.addVars(facilities, vtype=GRB.BINARY, name="y")

    # x[i, j] = 1 if resource i is assigned to facility j
    x = model.addVars(resources, facilities, vtype=GRB.BINARY, name="x")

    # Objective: minimize number of facilities used
    model.setObjective(gp.quicksum(y[j] for j in facilities), GRB.MINIMIZE)

    # Each resource assigned to exactly one facility
    for i in resources:
        model.addConstr(gp.quicksum(x[i, j] for j in facilities) == 1, name=f"assign_{i}")

    # Capacity constraints
    for j in facilities:
        model.addConstr(
            gp.quicksum(resource_weights[i] * x[i, j] for i in resources) <= facility_capacity * y[j],
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