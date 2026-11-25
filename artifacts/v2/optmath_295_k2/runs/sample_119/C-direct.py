import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit = params["profit"]
    holding_cost = params["holding_cost"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    grinder_time = params["grinder_time"]
    drill_time = params["drill_time"]
    borer_time = params["borer_time"]
    inventory_limit = params["inventory_limit"]
    sales_limit = params["sales_limit"]
    target_inventory = params["target_inventory"]

    products = range(4)
    periods = range(6)

    # Normalize capacities to per-period lists regardless of input shape
    def to_period_list(val, n_periods):
        if hasattr(val, "__len__") and not isinstance(val, str):
            return list(val)
        return [val] * n_periods

    grinder_cap = to_period_list(grinder_capacity, 6)
    drill_cap = to_period_list(drill_capacity, 6)
    borer_cap = to_period_list(borer_capacity, 6)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    produce = model.addVars(products, periods, lb=0.0, name="produce")
    inventory = model.addVars(products, periods, lb=0.0, name="inventory")
    sell = model.addVars(products, periods, lb=0.0, name="sell")

    # Objective: maximize profit from sales minus holding costs
    model.setObjective(
        gp.quicksum(profit[p] * sell[p, t] for p in products for t in periods)
        - gp.quicksum(holding_cost * inventory[p, t] for p in products for t in periods),
        GRB.MAXIMIZE
    )

    # Inventory balance constraints
    for p in products:
        for t in periods:
            if t == 0:
                model.addConstr(produce[p, t] == sell[p, t] + inventory[p, t])
            else:
                model.addConstr(inventory[p, t - 1] + produce[p, t] == sell[p, t] + inventory[p, t])

    # Machine capacity constraints
    for t in periods:
        model.addConstr(
            gp.quicksum(grinder_time[p] * produce[p, t] for p in products) <= grinder_cap[t]
        )
        model.addConstr(
            gp.quicksum(drill_time[p] * produce[p, t] for p in products) <= drill_cap[t]
        )
        model.addConstr(
            gp.quicksum(borer_time[p] * produce[p, t] for p in products) <= borer_cap[t]
        )

    # Inventory limit constraints
    for p in products:
        for t in periods:
            model.addConstr(inventory[p, t] <= inventory_limit[p])

    # Sales limit constraints
    for p in products:
        for t in periods:
            model.addConstr(sell[p, t] <= sales_limit[p][t])

    # Target inventory at end of period 5
    for p in products:
        model.addConstr(inventory[p, 5] == target_inventory[p])

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}