import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost_per_unit_per_period"]
    grinder_hours = params["grinder_hours"]
    drill_hours = params["drill_hours"]
    borer_hours = params["borer_hours"]
    machine_time_grinder = params["machine_time_grinder"]
    machine_time_drill = params["machine_time_drill"]
    machine_time_borer = params["machine_time_borer"]
    inventory_capacity = params["inventory_capacity"]
    sales_limit = params["sales_limit"]
    target_final_inventory = params["target_final_inventory"]

    products = range(3)
    periods = range(5)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    production = model.addVars(products, periods, lb=0.0, name="production")
    inventory = model.addVars(products, periods, lb=0.0, name="inventory")
    sales = model.addVars(products, periods, lb=0.0, name="sales")

    model.setObjective(
        gp.quicksum(profit_per_unit[p] * sales[p, t] for p in products for t in periods)
        - gp.quicksum(holding_cost * inventory[p, t] for p in products for t in periods),
        GRB.MAXIMIZE
    )

    for p in products:
        model.addConstr(
            production[p, 0] == sales[p, 0] + inventory[p, 0],
            name=f"balance_p{p}_t0"
        )
        for t in range(1, 5):
            model.addConstr(
                inventory[p, t-1] + production[p, t] == sales[p, t] + inventory[p, t],
                name=f"balance_p{p}_t{t}"
            )

    for t in periods:
        model.addConstr(
            gp.quicksum(machine_time_grinder[p] * production[p, t] for p in products) <= grinder_hours[t],
            name=f"grinder_t{t}"
        )
        model.addConstr(
            gp.quicksum(machine_time_drill[p] * production[p, t] for p in products) <= drill_hours[t],
            name=f"drill_t{t}"
        )
        model.addConstr(
            gp.quicksum(machine_time_borer[p] * production[p, t] for p in products) <= borer_hours[t],
            name=f"borer_t{t}"
        )

    # inventory_capacity is a single scalar shared across all products and periods
    inv_cap = inventory_capacity if not hasattr(inventory_capacity, '__len__') else None
    for p in products:
        for t in periods:
            if inv_cap is not None:
                cap = inv_cap
            else:
                # could be a list indexed by product
                try:
                    cap = inventory_capacity[p]
                except TypeError:
                    cap = inventory_capacity
            model.addConstr(
                inventory[p, t] <= cap,
                name=f"inv_cap_p{p}_t{t}"
            )

    for p in products:
        for t in periods:
            model.addConstr(
                sales[p, t] <= sales_limit[p][t],
                name=f"sales_limit_p{p}_t{t}"
            )

    for p in products:
        model.addConstr(
            inventory[p, 4] == target_final_inventory[p],
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
        return {"objective": None, "status": f"status_{model.Status}"}