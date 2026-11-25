import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_ordering_cost = params["fixed_ordering_cost"]
    variable_ordering_cost = params["variable_ordering_cost"]
    inventory_holding_cost = params["inventory_holding_cost"]
    demand = params["demand"]
    max_order_quantity = params["max_order_quantity"]
    initial_inventory = params["initial_inventory"]
    final_inventory = params["final_inventory"]

    T = 14
    periods = range(T)  # 0-indexed: period i corresponds to period i+1

    model = gp.Model("lot_sizing")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # y[i]: binary, 1 if an order is placed in period i
    y = model.addVars(T, vtype=GRB.BINARY, name="y")
    # x[i]: quantity ordered in period i
    x = model.addVars(T, lb=0.0, name="x")
    # inv[i]: inventory at end of period i (after satisfying demand)
    inv = model.addVars(T, lb=0.0, name="inv")

    # Objective: minimize total fixed + variable ordering + holding costs
    model.setObjective(
        gp.quicksum(
            fixed_ordering_cost[i] * y[i]
            + variable_ordering_cost[i] * x[i]
            + inventory_holding_cost[i] * inv[i]
            for i in periods
        ),
        GRB.MINIMIZE
    )

    # Demand fulfillment constraints (inventory balance)
    for i in periods:
        prev_inv = initial_inventory if i == 0 else inv[i - 1]
        model.addConstr(
            prev_inv + x[i] == demand[i] + inv[i],
            name=f"balance_{i}"
        )

    # Order quantity limits: x[i] <= max_order_quantity * y[i]
    for i in periods:
        model.addConstr(
            x[i] <= max_order_quantity * y[i],
            name=f"max_order_{i}"
        )

    # Final inventory requirement
    model.addConstr(inv[T - 1] == final_inventory, name="final_inv")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}