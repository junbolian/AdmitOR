import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_unit = [float(x) for x in params["profit_per_unit"]]
    holding_cost = float(params["holding_cost"])
    machine_capacity = [float(x) for x in params["machine_capacity"]]
    time_grinders = [float(x) for x in params["time_grinders"]]
    time_drills = [float(x) for x in params["time_drills"]]
    time_borers = [float(x) for x in params["time_borers"]]
    inventory_limit = float(params["inventory_limit"])
    sales_limit = [[float(params["sales_limit"][p][t]) for t in range(6)] for p in range(4)]
    target_inventory = [float(x) for x in params["target_inventory"]]

    num_products = 4
    num_periods = 6
    products = range(num_products)
    periods = range(num_periods)

    model = gp.Model("factory_planning")
    model.setParam("OutputFlag", 0)

    produce = model.addVars(products, periods, lb=0.0, name="produce")
    inventory = model.addVars(products, periods, lb=0.0, name="inventory")
    sell = model.addVars(products, periods, lb=0.0, name="sell")

    revenue = gp.quicksum(profit_per_unit[p] * sell[p, t] for p in products for t in periods)
    holding = gp.quicksum(holding_cost * inventory[p, t] for p in products for t in periods)
    model.setObjective(revenue - holding, GRB.MAXIMIZE)

    for p in products:
        model.addConstr(
            produce[p, 0] == sell[p, 0] + inventory[p, 0],
            name=f"balance_init_p{p}"
        )
        for t in range(1, num_periods):
            model.addConstr(
                inventory[p, t - 1] + produce[p, t] == sell[p, t] + inventory[p, t],
                name=f"balance_p{p}_t{t}"
            )
        model.addConstr(
            inventory[p, num_periods - 1] == target_inventory[p],
            name=f"target_inv_p{p}"
        )

    for t in periods:
        model.addConstr(
            gp.quicksum(time_grinders[p] * produce[p, t] for p in products) <= machine_capacity[0],
            name=f"grinder_t{t}"
        )
        model.addConstr(
            gp.quicksum(time_drills[p] * produce[p, t] for p in products) <= machine_capacity[1],
            name=f"drill_t{t}"
        )
        model.addConstr(
            gp.quicksum(time_borers[p] * produce[p, t] for p in products) <= machine_capacity[2],
            name=f"borer_t{t}"
        )

    for p in products:
        for t in periods:
            model.addConstr(
                inventory[p, t] <= inventory_limit,
                name=f"inv_limit_p{p}_t{t}"
            )

    for p in products:
        for t in periods:
            model.addConstr(
                sell[p, t] <= sales_limit[p][t],
                name=f"sales_limit_p{p}_t{t}"
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