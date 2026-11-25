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
    sales_limit_p0 = params["sales_limit_p0"]  # list of 4 values
    sales_limit_p1 = params["sales_limit_p1"]  # list of 4 values
    target_inventory = params["target_inventory"]

    periods = range(4)
    products = range(2)

    profits = [profit_p0, profit_p1]
    sales_limits = [sales_limit_p0, sales_limit_p1]
    grind_hours = [grind_hours_p0, grind_hours_p1]
    drill_hours = [drill_hours_p0, drill_hours_p1]
    bore_hours = [bore_hours_p0, bore_hours_p1]

    model = gp.Model("factory")
    model.setParam("OutputFlag", 0)

    # Decision variables
    prod = model.addVars(products, periods, lb=0.0, name="prod")
    inv = model.addVars(products, periods, lb=0.0, ub=inventory_limit, name="inv")
    sales = model.addVars(products, periods, lb=0.0, name="sales")

    # Objective: maximize revenue minus holding costs
    model.setObjective(
        gp.quicksum(profits[p] * sales[p, t] for p in products for t in periods)
        - gp.quicksum(holding_cost * inv[p, t] for p in products for t in periods),
        GRB.MAXIMIZE
    )

    # Initial balance (Period 0): production = sales + inventory
    for p in products:
        model.addConstr(prod[p, 0] == sales[p, 0] + inv[p, 0], name=f"init_balance_p{p}")

    # Inventory balance (Periods 1-3)
    for p in products:
        for t in range(1, 4):
            model.addConstr(
                inv[p, t - 1] + prod[p, t] == sales[p, t] + inv[p, t],
                name=f"inv_balance_p{p}_t{t}"
            )

    # Machine capacity constraints
    for t in periods:
        model.addConstr(
            gp.quicksum(grind_hours[p] * prod[p, t] for p in products) <= grinder_capacity,
            name=f"grinder_t{t}"
        )
        model.addConstr(
            gp.quicksum(drill_hours[p] * prod[p, t] for p in products) <= drill_capacity,
            name=f"drill_t{t}"
        )
        model.addConstr(
            gp.quicksum(bore_hours[p] * prod[p, t] for p in products) <= borer_capacity,
            name=f"borer_t{t}"
        )

    # Sales limits
    for p in products:
        for t in periods:
            model.addConstr(
                sales[p, t] <= sales_limits[p][t],
                name=f"sales_limit_p{p}_t{t}"
            )

    # Target inventory at end of Period 3
    for p in products:
        model.addConstr(inv[p, 3] == target_inventory, name=f"target_inv_p{p}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}