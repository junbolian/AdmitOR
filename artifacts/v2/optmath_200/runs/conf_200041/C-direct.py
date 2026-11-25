import gurobipy as gp
from gurobipy import GRB

def solve(params):
    item_weights = params["item_weights"]
    bin_capacity = params["bin_capacity"]

    n_items = len(item_weights)
    n_bins = n_items  # upper bound: one bin per item

    model = gp.Model("bin_packing")
    model.setParam("OutputFlag", 0)

    # x[i, j] = 1 if item i is assigned to bin j
    x = model.addVars(n_items, n_bins, vtype=GRB.BINARY, name="x")
    # y[j] = 1 if bin j is used
    y = model.addVars(n_bins, vtype=GRB.BINARY, name="y")

    # Objective: minimize number of bins used
    model.setObjective(gp.quicksum(y[j] for j in range(n_bins)), GRB.MINIMIZE)

    # Each item must be assigned to exactly one bin
    for i in range(n_items):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n_bins)) == 1, name=f"assign_{i}")

    # Capacity constraints
    for j in range(n_bins):
        model.addConstr(
            gp.quicksum(item_weights[i] * x[i, j] for i in range(n_items)) <= bin_capacity * y[j],
            name=f"capacity_{j}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}