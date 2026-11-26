import gurobipy as gp
from gurobipy import GRB

def solve(params):
    setup_cost = params["setup_cost"]      # list of 4 values [A, B, C, D]
    production_cost = params["production_cost"]  # list of 4 values
    capacity = params["capacity"]          # list of 4 values
    demand = params["demand"]              # scalar

    devices = range(4)

    model = gp.Model("device_selection")
    model.setParam("OutputFlag", 0)

    # y[i] = 1 if device i is activated
    y = model.addVars(devices, vtype=GRB.BINARY, name="y")
    # x[i] = units produced on device i
    x = model.addVars(devices, vtype=GRB.CONTINUOUS, lb=0.0, name="x")

    # Objective: minimize total setup + production cost
    model.setObjective(
        gp.quicksum(setup_cost[i] * y[i] + production_cost[i] * x[i] for i in devices),
        GRB.MINIMIZE
    )

    # Meet demand
    model.addConstr(gp.quicksum(x[i] for i in devices) == demand, name="demand")

    # Capacity constraints: x[i] <= capacity[i] * y[i]
    for i in devices:
        model.addConstr(x[i] <= capacity[i] * y[i], name=f"capacity_{i}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}