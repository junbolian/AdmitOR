import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_p0 = params["profit_p0"]
    profit_p1 = params["profit_p1"]
    holding_cost = params["holding_cost"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    grind_hours_p0 = params["grind_hours_per_unit_p0"]
    grind_hours_p1 = params["grind_hours_per_unit_p1"]
    drill_hours_p0 = params["drill_hours_per_unit_p0"]
    drill_hours_p1 = params["drill_hours_per_unit_p1"]
    bore_hours_p0 = params["bore_hours_per_unit_p0"]
    bore_hours_p1 = params["bore_hours_per_unit_p1"]
    inventory_limit = params["inventory_limit"]
    sales_limit_p0 = params["sales_limit_p0"]
    sales_limit_p1 = params["sales_limit_p1"]
    target_inventory = params["target_inventory"]

    periods = range(4)
    products = range(2)

    profits = [profit_p0, profit_p1]
    grind_hours = [grind_hours_p0, grind_hours_p1]
    drill_hours = [drill_hours_p0, drill_hours_p1]
    bore_hours = [bore_hours_p0, bore_hours_p1]
    sales_limits = [sales_limit_p0, sales_limit_p1]

    model = gp.Model("factory_production")
    model.setParam("OutputFlag", 0)

    # Decision variables
    produce = model.addVars(products, periods, lb=0.0, name="produce")
    inventory = model.addVars(products, periods, lb=0.0, ub=inventory_limit, name="inventory")
    sales = model.addVars(products, periods, lb=0.0, name="sales")

    # Sales limits per product per period
    for t in periods:
        model.addConstr(sales[0, t] <= sales_limits[0][t], name=f"sales_lim_p0_t{t}")
        model.addConstr(sales[1, t] <= sales_limits[1][t], name=f"sales_lim_p1_t{t}")

    # Inventory balance constraints
    for p in products:
        # Period 0: production = sales + inventory
        model.addConstr(
            produce[p, 0] == sales[p, 0] + inventory[p, 0],
            name=f"balance_p{p}_t0"
        )
        # Periods 1-3: prev inventory + production = sales + inventory
        for t in range(1, 4):
            model.addConstr(
                inventory[p, t - 1] + produce[p, t] == sales[p, t] + inventory[p, t],
                name=f"balance_p{p}_t{t}"
            )

    # Target inventory at end of period 3
    for p in products:
        model.addConstr(inventory[p, 3] == target_inventory, name=f"target_inv_p{p}")

    # Machine capacity constraints per period
    for t in periods:
        model.addConstr(
            gp.quicksum(grind_hours[p] * produce[p, t] for p in products) <= grinder_capacity,
            name=f"grinder_t{t}"
        )
        model.addConstr(
            gp.quicksum(drill_hours[p] * produce[p, t] for p in products) <= drill_capacity,
            name=f"drill_t{t}"
        )
        model.addConstr(
            gp.quicksum(bore_hours[p] * produce[p, t] for p in products) <= borer_capacity,
            name=f"borer_t{t}"
        )

    # Objective: maximize revenue from sales minus holding costs
    revenue = gp.quicksum(profits[p] * sales[p, t] for p in products for t in periods)
    holding = gp.quicksum(holding_cost * inventory[p, t] for p in products for t in periods)
    model.setObjective(revenue - holding, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}