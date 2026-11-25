import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_ordering_costs = params["fixed_ordering_costs"]
    variable_ordering_costs = params["variable_ordering_costs"]
    inventory_holding_costs = params["inventory_holding_costs"]
    demand = params["demand"]
    order_capacity = params["order_capacity"]
    initial_inventory = params["initial_inventory"]
    final_inventory = params["final_inventory"]

    T = len(demand)
    periods = range(T)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    order_placed = model.addVars(periods, vtype=GRB.BINARY, name="order_placed")
    order_qty = model.addVars(periods, lb=0.0, name="order_qty")
    inventory = model.addVars(periods, lb=0.0, name="inventory")

    # Objective: minimize total fixed + variable ordering + holding costs
    model.setObjective(
        gp.quicksum(
            fixed_ordering_costs[t] * order_placed[t]
            + variable_ordering_costs[t] * order_qty[t]
            + inventory_holding_costs[t] * inventory[t]
            for t in periods
        ),
        GRB.MINIMIZE
    )

    # Demand fulfillment (inventory balance)
    for t in periods:
        prev_inv = initial_inventory if t == 0 else inventory[t - 1]
        model.addConstr(
            prev_inv + order_qty[t] == demand[t] + inventory[t],
            name=f"balance_{t}"
        )

    # Order quantity upper bound (only if order is placed)
    for t in periods:
        model.addConstr(
            order_qty[t] <= order_capacity * order_placed[t],
            name=f"capacity_{t}"
        )

    # Final inventory requirement
    model.addConstr(inventory[T - 1] == final_inventory, name="final_inv")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}