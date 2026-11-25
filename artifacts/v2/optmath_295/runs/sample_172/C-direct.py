import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Read and normalize params
    profit_per_unit = list(params["profit_per_unit"])
    holding_cost = float(params["holding_cost_per_unit_per_period"])

    # machine_capacity_hours: shape (3, 5) — rows=machine, cols=period
    machine_capacity_raw = params["machine_capacity_hours"]
    machine_capacity = [[float(machine_capacity_raw[m][t]) for t in range(5)] for m in range(3)]

    # processing_time_hours: shape (3, 3) — rows=machine, cols=product
    processing_time_raw = params["processing_time_hours"]
    processing_time = [[float(processing_time_raw[m][p]) for p in range(3)] for m in range(3)]

    # max_inventory_per_product: shape (3,) — one per product
    max_inventory_raw = params["max_inventory_per_product"]
    # Handle scalar (single value for all) or list
    if hasattr(max_inventory_raw, '__len__') and not isinstance(max_inventory_raw, str):
        max_inventory = [float(max_inventory_raw[p]) for p in range(3)]
    else:
        max_inventory = [float(max_inventory_raw)] * 3

    # max_sales_per_product_per_period: shape (3, 5) — rows=product, cols=period
    max_sales_raw = params["max_sales_per_product_per_period"]
    max_sales = [[float(max_sales_raw[p][t]) for t in range(5)] for p in range(3)]

    # target_final_inventory: shape (3,) — one per product
    target_raw = params["target_final_inventory"]
    if hasattr(target_raw, '__len__') and not isinstance(target_raw, str):
        target_final_inventory = [float(target_raw[p]) for p in range(3)]
    else:
        target_final_inventory = [float(target_raw)] * 3

    num_products = 3
    num_periods = 5
    num_machines = 3

    products = range(num_products)
    periods = range(num_periods)
    machines = range(num_machines)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    produce = model.addVars(num_products, num_periods, lb=0.0, name="produce")
    inventory = model.addVars(num_products, num_periods, lb=0.0, name="inventory")
    sales = model.addVars(num_products, num_periods, lb=0.0, name="sales")

    model.setObjective(
        gp.quicksum(profit_per_unit[p] * sales[p, t] for p in products for t in periods)
        - gp.quicksum(holding_cost * inventory[p, t] for p in products for t in periods),
        GRB.MAXIMIZE
    )

    # Initial balance (period 0): production = sales + inventory
    for p in products:
        model.addConstr(
            produce[p, 0] == sales[p, 0] + inventory[p, 0],
            name=f"initial_balance_p{p}"
        )

    # Inventory balance for periods 1..4
    for p in products:
        for t in range(1, num_periods):
            model.addConstr(
                inventory[p, t - 1] + produce[p, t] == sales[p, t] + inventory[p, t],
                name=f"inv_balance_p{p}_t{t}"
            )

    # Machine capacity constraints
    for m in machines:
        for t in periods:
            model.addConstr(
                gp.quicksum(processing_time[m][p] * produce[p, t] for p in products)
                <= machine_capacity[m][t],
                name=f"machine_cap_m{m}_t{t}"
            )

    # Inventory limits
    for p in products:
        for t in periods:
            model.addConstr(
                inventory[p, t] <= max_inventory[p],
                name=f"inv_limit_p{p}_t{t}"
            )

    # Sales limits
    for p in products:
        for t in periods:
            model.addConstr(
                sales[p, t] <= max_sales[p][t],
                name=f"sales_limit_p{p}_t{t}"
            )

    # Target final inventory at end of period 4
    for p in products:
        model.addConstr(
            inventory[p, num_periods - 1] == target_final_inventory[p],
            name=f"final_inv_p{p}"
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