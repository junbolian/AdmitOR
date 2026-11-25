import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacities = params["capacities"]
    weights = params["weights"]

    num_items = len(weights)
    num_dims = len(capacities)

    # Upper bound on slots needed: at most num_items slots (one per procedure)
    max_slots = num_items

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i][s] = 1 if procedure i is assigned to slot s
    x = model.addVars(num_items, max_slots, vtype=GRB.BINARY, name="x")
    # y[s] = 1 if slot s is used
    y = model.addVars(max_slots, vtype=GRB.BINARY, name="y")

    # Minimize number of used slots
    model.setObjective(gp.quicksum(y[s] for s in range(max_slots)), GRB.MINIMIZE)

    # Each procedure assigned to exactly one slot
    for i in range(num_items):
        model.addConstr(gp.quicksum(x[i, s] for s in range(max_slots)) == 1, name=f"assign_{i}")

    # Capacity constraints per slot per dimension
    for s in range(max_slots):
        for d in range(num_dims):
            model.addConstr(
                gp.quicksum(weights[i][d] * x[i, s] for i in range(num_items)) <= capacities[d] * y[s],
                name=f"cap_s{s}_d{d}"
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