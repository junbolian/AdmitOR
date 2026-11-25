import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost_per_unit = params["holding_cost_per_unit"]
    machine_capacity_grinder = params["machine_capacity_grinder"]
    machine_capacity_drill = params["machine_capacity_drill"]
    machine_capacity_borer = params["machine_capacity_borer"]
    prod_time_grinder = params["prod_time_grinder"]
    prod_time_drill = params["prod_time_drill"]
    prod_time_borer = params["prod_time_borer"]
    inventory_capacity = params["inventory_capacity"]
    sales_limit_prod0 = params["sales_limit_prod0"]
    sales_limit_prod1 = params["sales_limit_prod1"]
    target_inventory = params["target_inventory"]

    def _as_list(val, n):
        if isinstance(val, (list, tuple)):
            return list(val)
        return [val] * n

    num_products = 2
    num_periods = 4
    products = range(num_products)
    periods = range(num_periods)

    profit_per_unit = _as_list(profit_per_unit, num_products)
    prod_time_grinder = _as_list(prod_time_grinder, num_products)
    prod_time_drill = _as_list(prod_time_drill, num_products)
    prod_time_borer = _as_list(prod_time_borer, num_products)
    target_inventory = _as_list(target_inventory, num_products)

    model = gp.Model("factory_planning")
    model.setParam("OutputFlag", 0)

    production = model.addVars(num_products, num_periods, lb=0.0, name="production")
    inventory = model.addVars(num_products, num_periods, lb=0.0, name="inventory")
    sales = model.addVars(num_products, num_periods, lb=0.0, name="sales")

    model.setObjective(
        gp.quicksum(profit_per_unit[p] * sales[p, t] for p in products for t in periods)
        - gp.quicksum(holding_cost_per_unit * inventory[p, t] for p in products for t in periods),
        GRB.MAXIMIZE
    )

    for p in products:
        for t in periods:
            if t == 0:
                model.addConstr(
                    production[p, t] == sales[p, t] + inventory[p, t],
                    name=f"balance_p{p}_t{t}"
                )
            else:
                model.addConstr(
                    inventory[p, t - 1] + production[p, t] == sales[p, t] + inventory[p, t],
                    name=f"balance_p{p}_t{t}"
                )

    for t in periods:
        model.addConstr(
            gp.quicksum(prod_time_grinder[p] * production[p, t] for p in products) <= machine_capacity_grinder,
            name=f"grinder_t{t}"
        )
        model.addConstr(
            gp.quicksum(prod_time_drill[p] * production[p, t] for p in products) <= machine_capacity_drill,
            name=f"drill_t{t}"
        )
        model.addConstr(
            gp.quicksum(prod_time_borer[p] * production[p, t] for p in products) <= machine_capacity_borer,
            name=f"borer_t{t}"
        )

    for p in products:
        for t in periods:
            model.addConstr(
                inventory[p, t] <= inventory_capacity,
                name=f"inv_cap_p{p}_t{t}"
            )

    sales_limits = [sales_limit_prod0, sales_limit_prod1]
    for p in products:
        for t in periods:
            model.addConstr(
                sales[p, t] <= sales_limits[p][t],
                name=f"sales_lim_p{p}_t{t}"
            )

    for p in products:
        model.addConstr(
            inventory[p, num_periods - 1] == target_inventory[p],
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
        return {"objective": None, "status": f"solver_status_{model.Status}"}