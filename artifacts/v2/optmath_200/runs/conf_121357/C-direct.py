import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    machine_time = params["machine_time"]
    max_inventory = params["max_inventory"]
    max_sales = params["max_sales"]
    final_inventory = params["final_inventory"]

    num_products = 4
    num_periods = 6
    products = range(num_products)
    periods = range(num_periods)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    production = model.addVars(num_products, num_periods, lb=0.0, name="production")
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
                model.addConstr(production[p, t] == sales[p, t] + inventory[p, t])
            else:
                model.addConstr(inventory[p, t-1] + production[p, t] == sales[p, t] + inventory[p, t])

    # Machine capacity constraints
    # machine_time[product][machine]: 0=grinder, 1=drill, 2=borer
    for t in periods:
        model.addConstr(
            gp.quicksum(machine_time[p][0] * production[p, t] for p in products) <= grinder_capacity[t]
        )
        model.addConstr(
            gp.quicksum(machine_time[p][1] * production[p, t] for p in products) <= drill_capacity[t]
        )
        model.addConstr(
            gp.quicksum(machine_time[p][2] * production[p, t] for p in products) <= borer_capacity[t]
        )

    # Inventory upper bound
    for p in products:
        for t in periods:
            model.addConstr(inventory[p, t] <= max_inventory)

    # Sales upper bound
    for p in products:
        for t in periods:
            model.addConstr(sales[p, t] <= max_sales[p][t])

    # Final inventory requirement
    for p in products:
        model.addConstr(inventory[p, num_periods - 1] == final_inventory[p])

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}