import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_product0 = params["profit_product0"]
    profit_product1 = params["profit_product1"]
    holding_cost = params["holding_cost"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    time_product0_grinder = params["time_product0_grinder"]
    time_product0_drill = params["time_product0_drill"]
    time_product0_borer = params["time_product0_borer"]
    time_product1_grinder = params["time_product1_grinder"]
    time_product1_drill = params["time_product1_drill"]
    time_product1_borer = params["time_product1_borer"]
    inventory_limit = params["inventory_limit"]
    sales_limit_product0 = params["sales_limit_product0"]
    sales_limit_product1 = params["sales_limit_product1"]
    target_inventory = params["target_inventory"]

    n_periods = 4
    n_products = 2

    # sales_limit_productX is expected to be a list of 4 values
    sales_limits = [sales_limit_product0, sales_limit_product1]
    profits = [profit_product0, profit_product1]

    machine_capacities = [grinder_capacity, drill_capacity, borer_capacity]
    # time[product][machine]
    time_requirements = [
        [time_product0_grinder, time_product0_drill, time_product0_borer],
        [time_product1_grinder, time_product1_drill, time_product1_borer],
    ]

    model = gp.Model("factory_production")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # production[p][t]: units produced of product p in period t
    production = [[model.addVar(lb=0.0, name=f"prod_p{p}_t{t}")
                   for t in range(n_periods)] for p in range(n_products)]

    # inventory[p][t]: units stored of product p at end of period t
    inventory = [[model.addVar(lb=0.0, ub=inventory_limit, name=f"inv_p{p}_t{t}")
                  for t in range(n_periods)] for p in range(n_products)]

    # sales[p][t]: units sold of product p in period t
    sales = [[model.addVar(lb=0.0, ub=sales_limits[p][t], name=f"sales_p{p}_t{t}")
              for t in range(n_periods)] for p in range(n_products)]

    # Objective: maximize revenue from sales minus holding costs
    model.setObjective(
        gp.quicksum(profits[p] * sales[p][t]
                    for p in range(n_products) for t in range(n_periods))
        - gp.quicksum(holding_cost * inventory[p][t]
                      for p in range(n_products) for t in range(n_periods)),
        GRB.MAXIMIZE
    )

    # Inventory balance constraints
    for p in range(n_products):
        # Period 0: production = sales + inventory
        model.addConstr(
            production[p][0] == sales[p][0] + inventory[p][0],
            name=f"balance_p{p}_t0"
        )
        # Periods 1-3: prev_inventory + production = sales + inventory
        for t in range(1, n_periods):
            model.addConstr(
                inventory[p][t-1] + production[p][t] == sales[p][t] + inventory[p][t],
                name=f"balance_p{p}_t{t}"
            )

    # Machine capacity constraints
    machine_names = ["grinder", "drill", "borer"]
    for t in range(n_periods):
        for m_idx, (cap, m_name) in enumerate(zip(machine_capacities, machine_names)):
            model.addConstr(
                gp.quicksum(time_requirements[p][m_idx] * production[p][t]
                            for p in range(n_products)) <= cap,
                name=f"machine_{m_name}_t{t}"
            )

    # Target inventory at end of horizon (period 3)
    for p in range(n_products):
        model.addConstr(
            inventory[p][n_periods - 1] == target_inventory,
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