import gurobipy as gp
from gurobipy import GRB


def solve(params):
    capacity = params["capacity"]   # list of length num_dims
    weights = params["weights"]     # list of num_items lists, each of length num_dims

    num_items = len(weights)
    num_dims = len(capacity)

    # Upper bound on slots needed: in the worst case every item gets its own slot
    max_slots = num_items

    items = range(num_items)
    slots = range(max_slots)
    dims  = range(num_dims)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i, s] = 1 if campaign i is assigned to slot s
    x = model.addVars(items, slots, vtype=GRB.BINARY, name="x")
    # y[s] = 1 if slot s is used
    y = model.addVars(slots, vtype=GRB.BINARY, name="y")

    # Objective: minimize number of used slots
    model.setObjective(gp.quicksum(y[s] for s in slots), GRB.MINIMIZE)

    # Each campaign must be assigned to exactly one slot
    for i in items:
        model.addConstr(gp.quicksum(x[i, s] for s in slots) == 1, name=f"assign_{i}")

    # Capacity constraints per slot per dimension
    for s in slots:
        for d in dims:
            model.addConstr(
                gp.quicksum(weights[i][d] * x[i, s] for i in items) <= capacity[d] * y[s],
                name=f"cap_s{s}_d{d}"
            )

    # Symmetry-breaking: slot s can only be used if slot s-1 is used
    for s in range(1, max_slots):
        model.addConstr(y[s] <= y[s - 1], name=f"sym_{s}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}