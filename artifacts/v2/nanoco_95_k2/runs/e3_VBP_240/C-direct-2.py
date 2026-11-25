import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity_impressions = params["capacity_impressions"]
    capacity_cost = params["capacity_cost"]
    demand_impressions = params["demand_impressions"]  # list of 9 values
    demand_cost = params["demand_cost"]                # list of 9 values

    num_items = 9
    # Upper bound on slots needed: in the worst case each campaign gets its own slot
    num_slots = num_items

    items = range(num_items)
    slots = range(num_slots)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i, s] = 1 if campaign i is assigned to slot s
    x = model.addVars(num_items, num_slots, vtype=GRB.BINARY, name="x")
    # y[s] = 1 if slot s is used
    y = model.addVars(num_slots, vtype=GRB.BINARY, name="y")

    # Objective: minimize number of used slots
    model.setObjective(gp.quicksum(y[s] for s in slots), GRB.MINIMIZE)

    # Each campaign must be assigned to exactly one slot
    for i in items:
        model.addConstr(gp.quicksum(x[i, s] for s in slots) == 1, name=f"assign_{i}")

    # Capacity constraints per slot
    for s in slots:
        model.addConstr(
            gp.quicksum(demand_impressions[i] * x[i, s] for i in items) <= capacity_impressions * y[s],
            name=f"cap_imp_{s}"
        )
        model.addConstr(
            gp.quicksum(demand_cost[i] * x[i, s] for i in items) <= capacity_cost * y[s],
            name=f"cap_cost_{s}"
        )

    # Symmetry breaking: slot s can only be used if slot s-1 is used
    for s in range(1, num_slots):
        model.addConstr(y[s] <= y[s - 1], name=f"sym_{s}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}