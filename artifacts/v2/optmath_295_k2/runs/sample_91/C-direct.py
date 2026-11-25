import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit = [
        params["profit_per_unit_product_0"],
        params["profit_per_unit_product_1"],
        params["profit_per_unit_product_2"],
    ]
    holding_cost = params["holding_cost_per_unit_per_month"]

    machine_hours = {
        "grinders": params["machine_hours_available_grinders"],
        "drills":   params["machine_hours_available_drills"],
        "borers":   params["machine_hours_available_borers"],
    }

    machine_time = {
        "grinders": [
            params["time_grinders_product_0"],
            params["time_grinders_product_1"],
            params["time_grinders_product_2"],
        ],
        "drills": [
            params["time_drills_product_0"],
            params["time_drills_product_1"],
            params["time_drills_product_2"],
        ],
        "borers": [
            params["time_borers_product_0"],
            params["time_borers_product_1"],
            params["time_borers_product_2"],
        ],
    }

    max_inventory = params["max_inventory_per_product"]

    sales_limits = [
        params["sales_limits_product_0"],
        params["sales_limits_product_1"],
        params["sales_limits_product_2"],
    ]

    target_inventory = params["target_inventory_end_horizon"]

    products = range(3)
    months   = range(4)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    produce = {
        (p, t): model.addVar(lb=0.0, name=f"produce_{p}_{t}")
        for p in products for t in months
    }
    inventory = {
        (p, t): model.addVar(lb=0.0, ub=max_inventory, name=f"inventory_{p}_{t}")
        for p in products for t in months
    }
    sell = {
        (p, t): model.addVar(lb=0.0, ub=sales_limits[p][t], name=f"sell_{p}_{t}")
        for p in products for t in months
    }

    model.setObjective(
        gp.quicksum(profit[p] * sell[p, t] for p in products for t in months)
        - gp.quicksum(holding_cost * inventory[p, t] for p in products for t in months),
        GRB.MAXIMIZE,
    )

    for p in products:
        model.addConstr(
            produce[p, 0] == sell[p, 0] + inventory[p, 0],
            name=f"balance_{p}_0",
        )
        for t in range(1, 4):
            model.addConstr(
                inventory[p, t - 1] + produce[p, t] == sell[p, t] + inventory[p, t],
                name=f"balance_{p}_{t}",
            )

    for machine, hours_list in machine_hours.items():
        times = machine_time[machine]
        for t in months:
            model.addConstr(
                gp.quicksum(times[p] * produce[p, t] for p in products) <= hours_list[t],
                name=f"capacity_{machine}_{t}",
            )

    # target_inventory_end_horizon is a scalar applied to all products
    for p in products:
        model.addConstr(
            inventory[p, 3] == target_inventory,
            name=f"target_inventory_{p}",
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}