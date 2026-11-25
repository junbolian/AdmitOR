import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacities = params["capacities"]
    weights = params["weights"]

    num_items = len(weights)
    num_dims = len(capacities)

    # Upper bound on slots needed: at most num_items slots (one per procedure)
    max_slots = num_items

    items = range(num_items)
    slots = range(max_slots)
    dims = range(num_dims)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i, s] = 1 if procedure i is assigned to slot s
    x = model.addVars(num_items, max_slots, vtype=GRB.BINARY, name="x")
    # y[s] = 1 if slot s is used
    y = model.addVars(max_slots, vtype=GRB.BINARY, name="y")

    # Objective: minimize number of used slots
    model.setObjective(gp.quicksum(y[s] for s in slots), GRB.MINIMIZE)

    # Each procedure assigned to exactly one slot
    for i in items:
        model.addConstr(gp.quicksum(x[i, s] for s in slots) == 1, name=f"assign_{i}")

    # Capacity constraints per slot per dimension
    for s in slots:
        for d in dims:
            model.addConstr(
                gp.quicksum(weights[i][d] * x[i, s] for i in items) <= capacities[d] * y[s],
                name=f"cap_{s}_{d}"
            )

    # Symmetry breaking: slot s can only be used if slot s-1 is used
    for s in range(1, max_slots):
        model.addConstr(y[s] <= y[s - 1], name=f"sym_{s}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}