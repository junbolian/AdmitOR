import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_unit = params["profit_per_unit"]          # list of length 3
    holding_cost = params["holding_cost_per_unit"]        # scalar
    grinder_hours = params["grinder_hours_per_unit"]      # list of length 3
    drill_hours = params["drill_hours_per_unit"]          # list of length 3
    borer_hours = params["borer_hours_per_unit"]          # list of length 3
    grinder_cap = params["grinder_capacity"]              # list of length 4
    drill_cap = params["drill_capacity"]                  # list of length 4
    borer_cap = params["borer_capacity"]                  # list of length 4
    inventory_limit = params["inventory_limit"]           # scalar (same for all products)
    sales_limit = params["sales_limit"]                   # 4x3 nested list
    final_inventory = params["final_inventory"]           # list of length 3

    periods = range(4)
    products = range(3)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    produce = model.addVars(periods, products, lb=0.0, name="produce")
    sell = model.addVars(periods, products, lb=0.0, name="sell")
    inventory = model.addVars(periods, products, lb=0.0, name="inventory")

    # Objective: maximize profit from sales minus holding costs
    model.setObjective(
        gp.quicksum(profit_per_unit[p] * sell[t, p] for t in periods for p in products)
        - gp.quicksum(holding_cost * inventory[t, p] for t in periods for p in products),
        GRB.MAXIMIZE
    )

    # Inventory balance constraints
    for p in products:
        # Period 0: production = sales + inventory
        model.addConstr(produce[0, p] == sell[0, p] + inventory[0, p])
        # Periods 1-3: prev inventory + production = sales + inventory
        for t in range(1, 4):
            model.addConstr(inventory[t-1, p] + produce[t, p] == sell[t, p] + inventory[t, p])

    # Machine capacity constraints
    for t in periods:
        model.addConstr(
            gp.quicksum(grinder_hours[p] * produce[t, p] for p in products) <= grinder_cap[t]
        )
        model.addConstr(
            gp.quicksum(drill_hours[p] * produce[t, p] for p in products) <= drill_cap[t]
        )
        model.addConstr(
            gp.quicksum(borer_hours[p] * produce[t, p] for p in products) <= borer_cap[t]
        )

    # Inventory limits (scalar applies to all products and periods)
    for t in periods:
        for p in products:
            model.addConstr(inventory[t, p] <= inventory_limit)

    # Sales limits
    for t in periods:
        for p in products:
            model.addConstr(sell[t, p] <= sales_limit[t][p])

    # Final inventory requirement
    for p in products:
        model.addConstr(inventory[3, p] == final_inventory[p])

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}