import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost_per_unit = params["holding_cost_per_unit"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    machine_hours_product0 = params["machine_hours_product0"]
    machine_hours_product1 = params["machine_hours_product1"]
    machine_hours_product2 = params["machine_hours_product2"]
    max_inventory_per_product = params["max_inventory_per_product"]
    sales_limit_product0 = params["sales_limit_product0"]
    sales_limit_product1 = params["sales_limit_product1"]
    sales_limit_product2 = params["sales_limit_product2"]
    target_inventory_end = params["target_inventory_end"]

    num_products = 3
    num_periods = 5
    products = range(num_products)
    periods = range(num_periods)

    machine_hours = [
        machine_hours_product0,
        machine_hours_product1,
        machine_hours_product2,
    ]

    sales_limits = [
        sales_limit_product0,
        sales_limit_product1,
        sales_limit_product2,
    ]

    # machine capacities per period: [grinder, drill, borer]
    # grinder_capacity, drill_capacity, borer_capacity may be lists (per period) or scalars
    def get_capacity(cap, t):
        if hasattr(cap, '__len__'):
            return cap[t]
        return cap

    model = gp.Model("factory_production")
    model.setParam("OutputFlag", 0)

    # Decision variables
    produce = model.addVars(num_products, num_periods, lb=0.0, name="produce")
    inventory = model.addVars(num_products, num_periods, lb=0.0, name="inventory")
    sales = model.addVars(num_products, num_periods, lb=0.0, name="sales")

    # Objective: maximize revenue from sales minus holding costs
    model.setObjective(
        gp.quicksum(
            profit_per_unit[p] * sales[p, t]
            for p in products for t in periods
        )
        - gp.quicksum(
            holding_cost_per_unit * inventory[p, t]
            for p in products for t in periods
        ),
        GRB.MAXIMIZE
    )

    # Inventory balance constraints
    for p in products:
        for t in periods:
            if t == 0:
                # Initial balance: production = sales + inventory
                model.addConstr(
                    produce[p, t] == sales[p, t] + inventory[p, t],
                    name=f"balance_p{p}_t{t}"
                )
            else:
                # inventory[t-1] + production[t] = sales[t] + inventory[t]
                model.addConstr(
                    inventory[p, t - 1] + produce[p, t] == sales[p, t] + inventory[p, t],
                    name=f"balance_p{p}_t{t}"
                )

    # Machine capacity constraints
    num_machines = 3
    capacities = [grinder_capacity, drill_capacity, borer_capacity]

    for t in periods:
        for m in range(num_machines):
            cap = get_capacity(capacities[m], t)
            model.addConstr(
                gp.quicksum(machine_hours[p][m] * produce[p, t] for p in products) <= cap,
                name=f"machine_m{m}_t{t}"
            )

    # Inventory limits
    for p in products:
        for t in periods:
            inv_limit = max_inventory_per_product[p] if hasattr(max_inventory_per_product, '__len__') else max_inventory_per_product
            model.addConstr(inventory[p, t] <= inv_limit, name=f"inv_limit_p{p}_t{t}")

    # Sales limits
    for p in products:
        for t in periods:
            model.addConstr(sales[p, t] <= sales_limits[p][t], name=f"sales_limit_p{p}_t{t}")

    # Target inventory at end of period 4
    for p in products:
        target = target_inventory_end[p] if hasattr(target_inventory_end, '__len__') else target_inventory_end
        model.addConstr(inventory[p, num_periods - 1] == target, name=f"target_inv_p{p}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}