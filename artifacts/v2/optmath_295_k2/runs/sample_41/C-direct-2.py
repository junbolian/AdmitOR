import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit = [
        params["profit_product0"],
        params["profit_product1"],
        params["profit_product2"],
    ]
    holding_cost = params["holding_cost"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    grinder_hours = params["grinder_hours_per_unit"]
    drill_hours = params["drill_hours_per_unit"]
    borer_hours = params["borer_hours_per_unit"]
    inventory_capacity = params["inventory_capacity"]
    sales_limit = [
        params["sales_limit_product0"],
        params["sales_limit_product1"],
        params["sales_limit_product2"],
    ]
    final_target = params["final_inventory_target"]

    products = range(3)
    periods = range(4)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    produce = {
        (p, t): model.addVar(lb=0, name=f"produce_{p}_{t}")
        for p in products for t in periods
    }
    inventory = {
        (p, t): model.addVar(lb=0, ub=inventory_capacity, name=f"inventory_{p}_{t}")
        for p in products for t in periods
    }
    sales = {
        (p, t): model.addVar(lb=0, ub=sales_limit[p][t], name=f"sales_{p}_{t}")
        for p in products for t in periods
    }

    # Objective: maximize profit from sales minus holding costs
    model.setObjective(
        gp.quicksum(profit[p] * sales[p, t] for p in products for t in periods)
        - gp.quicksum(holding_cost * inventory[p, t] for p in products for t in periods),
        GRB.MAXIMIZE,
    )

    # Inventory balance constraints
    for p in products:
        # Period 0: production = sales + inventory (no initial stock)
        model.addConstr(
            produce[p, 0] == sales[p, 0] + inventory[p, 0],
            name=f"balance_{p}_0",
        )
        # Periods 1-3: previous inventory + production = sales + inventory
        for t in range(1, 4):
            model.addConstr(
                inventory[p, t - 1] + produce[p, t] == sales[p, t] + inventory[p, t],
                name=f"balance_{p}_{t}",
            )

    # Machine capacity constraints
    for t in periods:
        model.addConstr(
            gp.quicksum(grinder_hours[p] * produce[p, t] for p in products) <= grinder_capacity,
            name=f"grinder_{t}",
        )
        model.addConstr(
            gp.quicksum(drill_hours[p] * produce[p, t] for p in products) <= drill_capacity,
            name=f"drill_{t}",
        )
        model.addConstr(
            gp.quicksum(borer_hours[p] * produce[p, t] for p in products) <= borer_capacity,
            name=f"borer_{t}",
        )

    # Final inventory target
    for p in products:
        model.addConstr(
            inventory[p, 3] == final_target,
            name=f"final_inventory_{p}",
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