import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    grinder_hours_per_unit = params["grinder_hours_per_unit"]
    drill_hours_per_unit = params["drill_hours_per_unit"]
    borer_hours_per_unit = params["borer_hours_per_unit"]
    inventory_limit = params["inventory_limit"]
    sales_limit_product0 = params["sales_limit_product0"]
    sales_limit_product1 = params["sales_limit_product1"]
    target_inventory = params["target_inventory"]

    products = [0, 1]
    periods = [0, 1, 2, 3]

    # target_inventory may be a scalar (same for all products) or indexable per product
    def get_target(p):
        try:
            return target_inventory[p]
        except (TypeError, KeyError):
            return target_inventory

    model = gp.Model("factory_planning")
    model.setParam("OutputFlag", 0)

    # Decision variables
    produce = model.addVars(products, periods, lb=0.0, name="produce")
    inventory = model.addVars(products, periods, lb=0.0, name="inventory")
    sell = model.addVars(products, periods, lb=0.0, name="sell")

    # Objective: maximize profit from sales minus holding costs
    model.setObjective(
        gp.quicksum(profit_per_unit[p] * sell[p, t] for p in products for t in periods)
        - holding_cost * gp.quicksum(inventory[p, t] for p in products for t in periods),
        GRB.MAXIMIZE
    )

    # Inventory balance constraints
    for p in products:
        for t in periods:
            if t == 0:
                model.addConstr(
                    produce[p, t] == sell[p, t] + inventory[p, t],
                    name=f"balance_p{p}_t{t}"
                )
            else:
                model.addConstr(
                    inventory[p, t - 1] + produce[p, t] == sell[p, t] + inventory[p, t],
                    name=f"balance_p{p}_t{t}"
                )

    # Machine capacity constraints
    for t in periods:
        model.addConstr(
            gp.quicksum(grinder_hours_per_unit[p] * produce[p, t] for p in products) <= grinder_capacity,
            name=f"grinder_t{t}"
        )
        model.addConstr(
            gp.quicksum(drill_hours_per_unit[p] * produce[p, t] for p in products) <= drill_capacity,
            name=f"drill_t{t}"
        )
        model.addConstr(
            gp.quicksum(borer_hours_per_unit[p] * produce[p, t] for p in products) <= borer_capacity,
            name=f"borer_t{t}"
        )

    # Inventory limits
    for p in products:
        for t in periods:
            model.addConstr(inventory[p, t] <= inventory_limit, name=f"inv_limit_p{p}_t{t}")

    # Sales limits
    sales_limits = {0: sales_limit_product0, 1: sales_limit_product1}
    for p in products:
        for t in periods:
            model.addConstr(sell[p, t] <= sales_limits[p][t], name=f"sales_limit_p{p}_t{t}")

    # Target inventory at end of period 3
    for p in products:
        model.addConstr(inventory[p, 3] == get_target(p), name=f"target_inv_p{p}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}