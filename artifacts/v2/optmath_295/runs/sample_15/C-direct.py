import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_p0 = params["profit_p0"]
    profit_p1 = params["profit_p1"]
    holding_cost = params["holding_cost"]
    grinder_hours_per_unit = params["grinder_hours_per_unit"]
    drill_hours_per_unit = params["drill_hours_per_unit"]
    borer_hours_per_unit_p0 = params["borer_hours_per_unit_p0"]
    borer_hours_per_unit_p1 = params["borer_hours_per_unit_p1"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    inventory_limit = params["inventory_limit"]
    sales_limit_p0 = params["sales_limit_p0"]
    sales_limit_p1 = params["sales_limit_p1"]
    target_inventory = params["target_inventory"]

    periods = range(4)
    products = range(2)
    profits = [profit_p0, profit_p1]
    sales_limits = [sales_limit_p0, sales_limit_p1]
    borer_hours = [borer_hours_per_unit_p0, borer_hours_per_unit_p1]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    produce = model.addVars(products, periods, lb=0.0, name="produce")
    inventory = model.addVars(products, periods, lb=0.0, ub=inventory_limit, name="inventory")
    sales = model.addVars(products, periods, lb=0.0, name="sales")

    # Objective: maximize revenue minus holding costs
    model.setObjective(
        gp.quicksum(profits[p] * sales[p, t] for p in products for t in periods)
        - gp.quicksum(holding_cost * inventory[p, t] for p in products for t in periods),
        GRB.MAXIMIZE
    )

    # Inventory balance constraints
    for p in products:
        for t in periods:
            if t == 0:
                model.addConstr(produce[p, t] == sales[p, t] + inventory[p, t],
                                name=f"balance_p{p}_t{t}")
            else:
                model.addConstr(inventory[p, t-1] + produce[p, t] == sales[p, t] + inventory[p, t],
                                name=f"balance_p{p}_t{t}")

    # Machine capacity constraints
    for t in periods:
        model.addConstr(
            gp.quicksum(grinder_hours_per_unit * produce[p, t] for p in products) <= grinder_capacity,
            name=f"grinder_t{t}"
        )
        model.addConstr(
            gp.quicksum(drill_hours_per_unit * produce[p, t] for p in products) <= drill_capacity,
            name=f"drill_t{t}"
        )
        model.addConstr(
            gp.quicksum(borer_hours[p] * produce[p, t] for p in products) <= borer_capacity,
            name=f"borer_t{t}"
        )

    # Sales limits
    for p in products:
        for t in periods:
            model.addConstr(sales[p, t] <= sales_limits[p][t], name=f"sales_limit_p{p}_t{t}")

    # Target inventory at end of period 3
    for p in products:
        model.addConstr(inventory[p, 3] == target_inventory, name=f"target_inv_p{p}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}