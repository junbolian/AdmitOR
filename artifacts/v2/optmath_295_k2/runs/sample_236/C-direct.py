import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n_items = 7
    weights = [params[f"item_weight_{i}"] for i in range(n_items)]
    capacity = params["bin_capacity"]
    n_bins = n_items  # upper bound: one bin per item

    model = gp.Model("warehouse_bin_packing")
    model.Params.OutputFlag = 0

    y = model.addVars(n_bins, vtype=GRB.BINARY, name="y")
    x = model.addVars(n_items, n_bins, vtype=GRB.BINARY, name="x")

    model.setObjective(gp.quicksum(y[j] for j in range(n_bins)), GRB.MINIMIZE)

    for i in range(n_items):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n_bins)) == 1, name=f"assign_{i}")

    for j in range(n_bins):
        model.addConstr(
            gp.quicksum(weights[i] * x[i, j] for i in range(n_items)) <= capacity * y[j],
            name=f"capacity_{j}",
        )

    for j in range(n_bins - 1):
        model.addConstr(y[j] >= y[j + 1], name=f"order_{j}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": "failed"}