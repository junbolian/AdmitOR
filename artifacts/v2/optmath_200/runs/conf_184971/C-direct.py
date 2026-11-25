import gurobipy as gp
from gurobipy import GRB

def solve(params):
    item_weights = params["item_weights"]
    container_capacity = params["container_capacity"]

    n_items = len(item_weights)
    n_containers = n_items  # upper bound: one item per container

    items = range(n_items)
    containers = range(n_containers)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i, j] = 1 if item i is assigned to container j
    x = model.addVars(items, containers, vtype=GRB.BINARY, name="x")
    # y[j] = 1 if container j is used
    y = model.addVars(containers, vtype=GRB.BINARY, name="y")

    # Minimize number of containers used
    model.setObjective(gp.quicksum(y[j] for j in containers), GRB.MINIMIZE)

    # Each item assigned to exactly one container
    for i in items:
        model.addConstr(gp.quicksum(x[i, j] for j in containers) == 1, name=f"assign_{i}")

    # Capacity constraint per container
    for j in containers:
        model.addConstr(
            gp.quicksum(item_weights[i] * x[i, j] for i in items) <= container_capacity * y[j],
            name=f"capacity_{j}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}