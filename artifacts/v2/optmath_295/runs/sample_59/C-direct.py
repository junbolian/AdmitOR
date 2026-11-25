import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_setup_cost = params["fixed_setup_cost"]
    variable_production_cost = params["variable_production_cost"]
    inventory_holding_cost = params["inventory_holding_cost"]
    backlogging_cost = params["backlogging_cost"]
    demand = params["demand"]
    production_capacity = params["production_capacity"]

    T = 6
    periods = range(T)  # 0-indexed: 0..5

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    y = model.addVars(T, vtype=GRB.BINARY, name="y")          # setup
    x = model.addVars(T, lb=0.0, name="x")                    # production
    inv = model.addVars(T, lb=0.0, name="inv")                 # inventory at end of period
    bl = model.addVars(T, lb=0.0, name="bl")                   # backlog at end of period

    # Objective
    model.setObjective(
        gp.quicksum(
            fixed_setup_cost[t] * y[t]
            + variable_production_cost[t] * x[t]
            + inventory_holding_cost[t] * inv[t]
            + backlogging_cost[t] * bl[t]
            for t in periods
        ),
        GRB.MINIMIZE
    )

    # Demand balance constraints
    # inv[t-1] + x[t] + bl[t-1] = demand[t] + inv[t] + bl[t]
    # with inv[-1] = 0, bl[-1] = 0
    for t in periods:
        inv_prev = inv[t - 1] if t > 0 else 0.0
        bl_prev = bl[t - 1] if t > 0 else 0.0
        model.addConstr(
            inv_prev + x[t] + bl_prev == demand[t] + inv[t] + bl[t],
            name=f"balance_{t}"
        )

    # Production capacity: x[t] <= capacity * y[t]
    for t in periods:
        model.addConstr(x[t] <= production_capacity * y[t], name=f"capacity_{t}")

    # No inventory or backlog at end of period 6 (last period, index 5)
    model.addConstr(inv[T - 1] == 0.0, name="inv_end")
    model.addConstr(bl[T - 1] == 0.0, name="bl_end")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}