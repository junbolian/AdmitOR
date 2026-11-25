import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost_per_unit_per_period"]
    machine_capacity = params["machine_capacity_per_period"]
    machine_time = params["machine_time_per_unit"]
    period0_borer_capacity = params["period0_borer_capacity"]
    inventory_limit = params["inventory_limit_per_product_per_period"]
    sales_limit = params["sales_limit"]
    target_inventory = params["target_inventory_end_period4"]

    num_products = 4
    num_periods = 5
    products = range(num_products)
    periods = range(num_periods)

    # Machine indices: 0=grinders, 1=drills, 2=borers
    num_machines = 3
    machines = range(num_machines)

    model = gp.Model("factory")
    model.setParam("OutputFlag", 0)

    # Decision variables
    produce = model.addVars(num_products, num_periods, lb=0.0, name="produce")
    inventory = model.addVars(num_products, num_periods, lb=0.0, name="inventory")
    sell = model.addVars(num_products, num_periods, lb=0.0, name="sell")

    # Objective: maximize revenue from sales minus holding costs
    model.setObjective(
        gp.quicksum(profit_per_unit[p] * sell[p, t] for p in products for t in periods)
        - gp.quicksum(holding_cost * inventory[p, t] for p in products for t in periods),
        GRB.MAXIMIZE
    )

    # Initial balance (Period 0): production = sales + inventory
    for p in products:
        model.addConstr(
            produce[p, 0] == sell[p, 0] + inventory[p, 0],
            name=f"init_balance_p{p}"
        )

    # Inventory balance for periods 1..4
    for p in products:
        for t in range(1, num_periods):
            model.addConstr(
                inventory[p, t - 1] + produce[p, t] == sell[p, t] + inventory[p, t],
                name=f"inv_balance_p{p}_t{t}"
            )

    # Machine capacity constraints
    for t in periods:
        for m in machines:
            if m == 2 and t == 0:
                # Borers unavailable in Period 0
                cap = period0_borer_capacity
            else:
                cap = machine_capacity[m]
            model.addConstr(
                gp.quicksum(machine_time[p][m] * produce[p, t] for p in products) <= cap,
                name=f"machine_cap_m{m}_t{t}"
            )

    # Inventory limits
    for p in products:
        for t in periods:
            model.addConstr(
                inventory[p, t] <= inventory_limit,
                name=f"inv_limit_p{p}_t{t}"
            )

    # Sales limits
    for p in products:
        for t in periods:
            model.addConstr(
                sell[p, t] <= sales_limit[p][t],
                name=f"sales_limit_p{p}_t{t}"
            )

    # Target inventory at end of Period 4
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