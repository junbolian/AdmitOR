import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost_raw = params["holding_cost_per_unit_per_period"]
    machine_hours = params["machine_hours_per_unit"]
    machine_capacity = params["machine_capacity_per_period"]
    max_inventory_raw = params["max_inventory_per_period"]
    sales_limit_p0 = params["sales_limit_product0"]
    sales_limit_p1 = params["sales_limit_product1"]
    target_inv = params["target_final_inventory"]

    # Normalize scalar-or-list params to scalars
    holding_cost = float(holding_cost_raw[0]) if hasattr(holding_cost_raw, '__len__') else float(holding_cost_raw)
    max_inventory = float(max_inventory_raw[0]) if hasattr(max_inventory_raw, '__len__') else float(max_inventory_raw)

    num_products = 2
    num_periods = 4
    num_machines = 3
    products = range(num_products)
    periods = range(num_periods)
    machines = range(num_machines)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    production = model.addVars(num_products, num_periods, lb=0.0, name="production")
    inventory = model.addVars(num_products, num_periods, lb=0.0, name="inventory")
    sales = model.addVars(num_products, num_periods, lb=0.0, name="sales")

    # Objective: maximize revenue minus holding costs
    obj = gp.quicksum(
        float(profit_per_unit[p]) * sales[p, t]
        for p in products for t in periods
    ) - gp.quicksum(
        holding_cost * inventory[p, t]
        for p in products for t in periods
    )
    model.setObjective(obj, GRB.MAXIMIZE)

    # Inventory balance
    for p in products:
        model.addConstr(
            production[p, 0] == sales[p, 0] + inventory[p, 0],
            name=f"balance_p{p}_t0"
        )
        for t in range(1, num_periods):
            model.addConstr(
                inventory[p, t - 1] + production[p, t] == sales[p, t] + inventory[p, t],
                name=f"balance_p{p}_t{t}"
            )

    # Machine capacity
    for mach in machines:
        cap = float(machine_capacity[mach])
        for t in periods:
            model.addConstr(
                gp.quicksum(
                    float(machine_hours[mach][p]) * production[p, t]
                    for p in products
                ) <= cap,
                name=f"capacity_m{mach}_t{t}"
            )

    # Inventory limits
    for p in products:
        for t in periods:
            model.addConstr(
                inventory[p, t] <= max_inventory,
                name=f"inv_limit_p{p}_t{t}"
            )

    # Sales limits
    for t in periods:
        model.addConstr(sales[0, t] <= float(sales_limit_p0[t]), name=f"sales_limit_p0_t{t}")
        model.addConstr(sales[1, t] <= float(sales_limit_p1[t]), name=f"sales_limit_p1_t{t}")

    # Target final inventory
    for p in products:
        model.addConstr(
            inventory[p, num_periods - 1] == float(target_inv[p]),
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