import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost_per_unit = params["holding_cost_per_unit"]
    machine_hours_grinders = params["machine_hours_grinders"]
    machine_hours_drills = params["machine_hours_drills"]
    machine_hours_borers = params["machine_hours_borers"]
    borer_hours_period0 = params["borer_hours_period0"]
    time_per_unit = params["time_per_unit"]
    inventory_capacity = params["inventory_capacity"]
    sales_limit = params["sales_limit"]
    target_inventory_end = params["target_inventory_end"]

    n_products = 4
    n_periods = 5

    model = gp.Model("factory_production")

    produce = {}
    sell = {}
    inv = {}
    for p in range(n_products):
        for t in range(n_periods):
            produce[p, t] = model.addVar(vtype=GRB.CONTINUOUS, name=f"produce_{p}_{t}")
            sell[p, t] = model.addVar(vtype=GRB.CONTINUOUS, name=f"sell_{p}_{t}")
            inv[p, t] = model.addVar(vtype=GRB.CONTINUOUS, name=f"inv_{p}_{t}")

    model.update()

    revenue = gp.quicksum(
        profit_per_unit[p] * sell[p, t]
        for p in range(n_products)
        for t in range(n_periods)
    )
    holding = gp.quicksum(
        holding_cost_per_unit * inv[p, t]
        for p in range(n_products)
        for t in range(n_periods)
    )
    model.setObjective(revenue - holding, GRB.MAXIMIZE)

    for p in range(n_products):
        model.addConstr(produce[p, 0] == sell[p, 0] + inv[p, 0], name=f"balance_0_{p}")

    for p in range(n_products):
        for t in range(1, n_periods):
            model.addConstr(
                inv[p, t - 1] + produce[p, t] == sell[p, t] + inv[p, t],
                name=f"balance_{t}_{p}",
            )

    for t in range(n_periods):
        model.addConstr(
            gp.quicksum(time_per_unit[p][0] * produce[p, t] for p in range(n_products))
            <= machine_hours_grinders,
            name=f"cap_grinder_{t}",
        )
        model.addConstr(
            gp.quicksum(time_per_unit[p][1] * produce[p, t] for p in range(n_products))
            <= machine_hours_drills,
            name=f"cap_drill_{t}",
        )
        borer_cap = borer_hours_period0 if t == 0 else machine_hours_borers
        model.addConstr(
            gp.quicksum(time_per_unit[p][2] * produce[p, t] for p in range(n_products))
            <= borer_cap,
            name=f"cap_borer_{t}",
        )

    for p in range(n_products):
        for t in range(n_periods):
            model.addConstr(inv[p, t] <= inventory_capacity, name=f"inv_cap_{p}_{t}")

    for p in range(n_products):
        for t in range(n_periods):
            model.addConstr(sell[p, t] <= sales_limit[p][t], name=f"sales_cap_{p}_{t}")

    for p in range(n_products):
        model.addConstr(
            inv[p, n_periods - 1] == target_inventory_end[p], name=f"target_{p}"
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": model.objVal, "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "failed"}