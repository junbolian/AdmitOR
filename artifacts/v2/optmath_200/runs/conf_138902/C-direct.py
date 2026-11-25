import gurobipy as gp
from gurobipy import GRB

def solve(params):
    bin_capacity = params["bin_capacity"]
    item_weights = params["item_weights"]

    num_items = len(item_weights)
    num_bins = num_items  # upper bound: one bin per item

    items = range(num_items)
    bins = range(num_bins)

    model = gp.Model("bin_packing")
    model.setParam("OutputFlag", 0)

    # x[i, j] = 1 if item i is assigned to bin j
    x = model.addVars(items, bins, vtype=GRB.BINARY, name="x")
    # y[j] = 1 if bin j is used
    y = model.addVars(bins, vtype=GRB.BINARY, name="y")

    # Objective: minimize number of bins used
    model.setObjective(gp.quicksum(y[j] for j in bins), GRB.MINIMIZE)

    # Each item must be assigned to exactly one bin
    for i in items:
        model.addConstr(gp.quicksum(x[i, j] for j in bins) == 1, name=f"assign_{i}")

    # Bin capacity constraints
    for j in bins:
        model.addConstr(
            gp.quicksum(item_weights[i] * x[i, j] for i in items) <= bin_capacity * y[j],
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