import gurobipy as gp
from gurobipy import GRB

def solve(params):
    spot_durations = params["spot_durations"]
    slot_capacity = params["slot_capacity"]

    n_spots = len(spot_durations)
    # Upper bound on slots needed: at most one per spot
    n_slots = n_spots

    spots = range(n_spots)
    slots = range(n_slots)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i, j] = 1 if spot i is assigned to slot j
    x = model.addVars(spots, slots, vtype=GRB.BINARY, name="x")
    # y[j] = 1 if slot j is used
    y = model.addVars(slots, vtype=GRB.BINARY, name="y")

    # Minimize number of slots used
    model.setObjective(gp.quicksum(y[j] for j in slots), GRB.MINIMIZE)

    # Each spot assigned to exactly one slot
    for i in spots:
        model.addConstr(gp.quicksum(x[i, j] for j in slots) == 1, name=f"assign_{i}")

    # Capacity constraint per slot
    for j in slots:
        model.addConstr(
            gp.quicksum(spot_durations[i] * x[i, j] for i in spots) <= slot_capacity * y[j],
            name=f"capacity_{j}"
        )

    # Symmetry breaking: slots used in order
    for j in range(n_slots - 1):
        model.addConstr(y[j] >= y[j + 1], name=f"sym_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}