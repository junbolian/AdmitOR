import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]
    prep_cost = params["prep_cost"]      # list or dict of 4 values [A, B, C, D]
    unit_cost = params["unit_cost"]      # list or dict of 4 values [A, B, C, D]
    capacity = params["capacity"]        # list or dict of 4 values [A, B, C, D]

    devices = ["A", "B", "C", "D"]

    # Normalize to indexed lists if needed
    if isinstance(prep_cost, dict):
        prep_cost = [prep_cost[d] for d in devices]
    if isinstance(unit_cost, dict):
        unit_cost = [unit_cost[d] for d in devices]
    if isinstance(capacity, dict):
        capacity = [capacity[d] for d in devices]

    model = gp.Model("device_selection")
    model.setParam("OutputFlag", 0)

    # y[i] = 1 if device i is enabled (binary)
    y = model.addVars(4, vtype=GRB.BINARY, name="y")

    # x[i] = units produced on device i (continuous)
    x = model.addVars(4, lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    # Objective: minimize total cost = sum of (prep_cost * y + unit_cost * x)
    model.setObjective(
        gp.quicksum(prep_cost[i] * y[i] + unit_cost[i] * x[i] for i in range(4)),
        GRB.MINIMIZE
    )

    # Demand constraint: total production must meet demand
    model.addConstr(gp.quicksum(x[i] for i in range(4)) >= demand, name="demand")

    # Capacity constraints: x[i] <= capacity[i] * y[i]
    for i in range(4):
        model.addConstr(x[i] <= capacity[i] * y[i], name=f"capacity_{devices[i]}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}