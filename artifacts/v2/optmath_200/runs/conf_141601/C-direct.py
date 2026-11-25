import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_unit_0 = params["profit_per_unit_0"]
    profit_per_unit_1 = params["profit_per_unit_1"]
    holding_cost_per_unit = params["holding_cost_per_unit"]
    grinder_hours_per_unit_0 = params["grinder_hours_per_unit_0"]
    grinder_hours_per_unit_1 = params["grinder_hours_per_unit_1"]
    drill_hours_per_unit_0 = params["drill_hours_per_unit_0"]
    drill_hours_per_unit_1 = params["drill_hours_per_unit_1"]
    borer_hours_per_unit_0 = params["borer_hours_per_unit_0"]
    borer_hours_per_unit_1 = params["borer_hours_per_unit_1"]
    grinder_capacity = params["grinder_capacity"]  # list of 4
    drill_capacity = params["drill_capacity"]        # list of 4
    borer_capacity = params["borer_capacity"]        # list of 4
    max_inventory_per_product = params["max_inventory_per_product"]
    max_sales_product_0 = params["max_sales_product_0"]  # list of 4
    max_sales_product_1 = params["max_sales_product_1"]  # list of 4
    terminal_inventory_per_product = params["terminal_inventory_per_product"]

    periods = range(4)
    products = range(2)

    model = gp.Model("production_inventory")
    model.setParam("OutputFlag", 0)

    # Decision variables
    production = {}
    inventory = {}
    sales = {}

    for p in products:
        for t in periods:
            production[p, t] = model.addVar(lb=0, name=f"prod_{p}_{t}")
            inventory[p, t] = model.addVar(lb=0, ub=max_inventory_per_product, name=f"inv_{p}_{t}")

    sales[0, 0] = model.addVar(lb=0, ub=max_sales_product_0[0], name="sales_0_0")
    sales[0, 1] = model.addVar(lb=0, ub=max_sales_product_0[1], name="sales_0_1")
    sales[0, 2] = model.addVar(lb=0, ub=max_sales_product_0[2], name="sales_0_2")
    sales[0, 3] = model.addVar(lb=0, ub=max_sales_product_0[3], name="sales_0_3")
    sales[1, 0] = model.addVar(lb=0, ub=max_sales_product_1[0], name="sales_1_0")
    sales[1, 1] = model.addVar(lb=0, ub=max_sales_product_1[1], name="sales_1_1")
    sales[1, 2] = model.addVar(lb=0, ub=max_sales_product_1[2], name="sales_1_2")
    sales[1, 3] = model.addVar(lb=0, ub=max_sales_product_1[3], name="sales_1_3")

    model.update()

    # Objective: maximize profit from sales minus holding costs
    obj = (gp.quicksum(profit_per_unit_0 * sales[0, t] for t in periods)
           + gp.quicksum(profit_per_unit_1 * sales[1, t] for t in periods)
           - gp.quicksum(holding_cost_per_unit * inventory[p, t] for p in products for t in periods))
    model.setObjective(obj, GRB.MAXIMIZE)

    # Inventory balance constraints
    for p in products:
        # Period 0: production = sales + inventory
        model.addConstr(production[p, 0] == sales[p, 0] + inventory[p, 0],
                        name=f"balance_{p}_0")
        # Periods 1-3: inventory[t-1] + production[t] = sales[t] + inventory[t]
        for t in range(1, 4):
            model.addConstr(inventory[p, t-1] + production[p, t] == sales[p, t] + inventory[p, t],
                            name=f"balance_{p}_{t}")

    # Terminal inventory constraints
    for p in products:
        model.addConstr(inventory[p, 3] == terminal_inventory_per_product,
                        name=f"terminal_{p}")

    # Machine capacity constraints
    for t in periods:
        # Grinder
        model.addConstr(
            grinder_hours_per_unit_0 * production[0, t] + grinder_hours_per_unit_1 * production[1, t] <= grinder_capacity[t],
            name=f"grinder_{t}"
        )
        # Drill
        model.addConstr(
            drill_hours_per_unit_0 * production[0, t] + drill_hours_per_unit_1 * production[1, t] <= drill_capacity[t],
            name=f"drill_{t}"
        )
        # Borer
        model.addConstr(
            borer_hours_per_unit_0 * production[0, t] + borer_hours_per_unit_1 * production[1, t] <= borer_capacity[t],
            name=f"borer_{t}"
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