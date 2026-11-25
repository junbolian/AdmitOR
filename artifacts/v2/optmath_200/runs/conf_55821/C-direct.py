import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost_per_unit_period"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    max_inventory = params["max_inventory"]
    target_inventory_period4 = params["target_inventory_period4"]
    sales_limit_product0 = params["sales_limit_product0"]
    sales_limit_product1 = params["sales_limit_product1"]
    sales_limit_product2 = params["sales_limit_product2"]
    sales_limit_product3 = params["sales_limit_product3"]

    num_products = 4
    num_periods = 5
    products = range(num_products)
    periods = range(num_periods)

    # Machine time per unit produced: grinder, drill, borer
    grinder_rate = [1, 1, 2, 2]
    drill_rate = [2, 2, 2, 2]
    borer_rate = [1, 1, 1, 1]

    # Sales limits indexed by [product][period]
    sales_limits = [
        sales_limit_product0,
        sales_limit_product1,
        sales_limit_product2,
        sales_limit_product3,
    ]

    # Normalize target_inventory_period4 to a per-product list
    if hasattr(target_inventory_period4, '__iter__') and not isinstance(target_inventory_period4, str):
        target_inv = list(target_inventory_period4)
    else:
        target_inv = [target_inventory_period4] * num_products

    # Normalize max_inventory to a per-product-period scalar or handle both cases
    # max_inventory is described as a scalar maximum per product per period
    if hasattr(max_inventory, '__iter__') and not isinstance(max_inventory, str):
        max_inv_list = list(max_inventory)
        def get_max_inv(p):
            return max_inv_list[p]
    else:
        def get_max_inv(p):
            return max_inventory

    model = gp.Model("manufacturing")
    model.setParam("OutputFlag", 0)

    # Decision variables
    produce = model.addVars(num_products, num_periods, lb=0.0, name="produce")
    inventory = model.addVars(num_products, num_periods, lb=0.0, name="inventory")
    sales = model.addVars(num_products, num_periods, lb=0.0, name="sales")

    # Objective: maximize profit - holding costs
    model.setObjective(
        gp.quicksum(profit_per_unit[p] * sales[p, t] for p in products for t in periods)
        - gp.quicksum(holding_cost * inventory[p, t] for p in products for t in periods),
        GRB.MAXIMIZE
    )

    # Inventory balance constraints
    for p in products:
        for t in periods:
            if t == 0:
                model.addConstr(
                    produce[p, t] == sales[p, t] + inventory[p, t],
                    name=f"balance_p{p}_t{t}"
                )
            else:
                model.addConstr(
                    inventory[p, t - 1] + produce[p, t] == sales[p, t] + inventory[p, t],
                    name=f"balance_p{p}_t{t}"
                )

    # Machine capacity constraints
    for t in periods:
        model.addConstr(
            gp.quicksum(grinder_rate[p] * produce[p, t] for p in products) <= grinder_capacity[t],
            name=f"grinder_t{t}"
        )
        model.addConstr(
            gp.quicksum(drill_rate[p] * produce[p, t] for p in products) <= drill_capacity[t],
            name=f"drill_t{t}"
        )
        model.addConstr(
            gp.quicksum(borer_rate[p] * produce[p, t] for p in products) <= borer_capacity[t],
            name=f"borer_t{t}"
        )

    # Inventory limits
    for p in products:
        for t in periods:
            model.addConstr(inventory[p, t] <= get_max_inv(p), name=f"inv_limit_p{p}_t{t}")

    # Sales limits
    for p in products:
        for t in periods:
            model.addConstr(sales[p, t] <= sales_limits[p][t], name=f"sales_limit_p{p}_t{t}")

    # Target inventory at end of period 4
    for p in products:
        model.addConstr(
            inventory[p, num_periods - 1] == target_inv[p],
            name=f"target_inv_p{p}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}