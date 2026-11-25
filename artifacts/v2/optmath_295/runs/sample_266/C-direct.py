import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost_per_unit = params["holding_cost_per_unit"]
    grinder_hours_per_unit = params["grinder_hours_per_unit"]
    drill_hours_per_unit = params["drill_hours_per_unit"]
    borer_hours_per_unit = params["borer_hours_per_unit"]
    grinder_capacity_per_period = params["grinder_capacity_per_period"]
    drill_capacity_per_period = params["drill_capacity_per_period"]
    borer_capacity_per_period = params["borer_capacity_per_period"]
    max_inventory_per_product = params["max_inventory_per_product"]
    max_sales_product_0 = params["max_sales_product_0"]
    max_sales_product_1 = params["max_sales_product_1"]
    max_sales_product_2 = params["max_sales_product_2"]
    terminal_inventory_target = params["terminal_inventory_target"]

    num_products = 3
    num_periods = 6
    products = range(num_products)
    periods = range(num_periods)

    max_sales = [max_sales_product_0, max_sales_product_1, max_sales_product_2]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    produce = model.addVars(num_products, num_periods, lb=0.0, name="produce")
    inventory = model.addVars(num_products, num_periods, lb=0.0, name="inventory")
    sell = model.addVars(num_products, num_periods, lb=0.0, name="sell")

    model.setObjective(
        gp.quicksum(profit_per_unit[p] * sell[p, t] for p in products for t in periods)
        - gp.quicksum(holding_cost_per_unit * inventory[p, t] for p in products for t in periods),
        GRB.MAXIMIZE
    )

    for p in products:
        for t in periods:
            if t == 0:
                model.addConstr(produce[p, t] == sell[p, t] + inventory[p, t])
            else:
                model.addConstr(inventory[p, t - 1] + produce[p, t] == sell[p, t] + inventory[p, t])

    for t in periods:
        model.addConstr(
            gp.quicksum(grinder_hours_per_unit[p] * produce[p, t] for p in products)
            <= grinder_capacity_per_period
        )
        drill_cap = 0.0 if t == 2 else drill_capacity_per_period
        model.addConstr(
            gp.quicksum(drill_hours_per_unit[p] * produce[p, t] for p in products)
            <= drill_cap
        )
        model.addConstr(
            gp.quicksum(borer_hours_per_unit[p] * produce[p, t] for p in products)
            <= borer_capacity_per_period
        )

    for p in products:
        for t in periods:
            model.addConstr(sell[p, t] <= max_sales[p][t])

    for p in products:
        for t in periods:
            model.addConstr(inventory[p, t] <= max_inventory_per_product)

    # terminal_inventory_target may be a scalar or a list; handle both
    for p in products:
        if hasattr(terminal_inventory_target, '__getitem__'):
            target = terminal_inventory_target[p]
        else:
            target = terminal_inventory_target
        model.addConstr(inventory[p, num_periods - 1] == target)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}