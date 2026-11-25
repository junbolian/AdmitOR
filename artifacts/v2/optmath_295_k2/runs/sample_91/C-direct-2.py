import gurobipy as gp
from gurobipy import GRB

def solve(params):
    products = [0, 1, 2]
    months = [0, 1, 2, 3]
    machine_names = ["grinders", "drills", "borers"]

    profit = {
        0: params["profit_per_unit_product_0"],
        1: params["profit_per_unit_product_1"],
        2: params["profit_per_unit_product_2"],
    }
    holding_cost = params["holding_cost_per_unit_per_month"]

    machine_hours = {
        "grinders": params["machine_hours_available_grinders"],
        "drills": params["machine_hours_available_drills"],
        "borers": params["machine_hours_available_borers"],
    }

    proc_time = {
        "grinders": {
            0: params["time_grinders_product_0"],
            1: params["time_grinders_product_1"],
            2: params["time_grinders_product_2"],
        },
        "drills": {
            0: params["time_drills_product_0"],
            1: params["time_drills_product_1"],
            2: params["time_drills_product_2"],
        },
        "borers": {
            0: params["time_borers_product_0"],
            1: params["time_borers_product_1"],
            2: params["time_borers_product_2"],
        },
    }

    max_inv = params["max_inventory_per_product"]

    sales_limits = {
        0: params["sales_limits_product_0"],
        1: params["sales_limits_product_1"],
        2: params["sales_limits_product_2"],
    }

    target_raw = params["target_inventory_end_horizon"]
    if isinstance(target_raw, (list, tuple)):
        target_inv = {p: target_raw[p] for p in products}
    else:
        target_inv = {p: target_raw for p in products}

    model = gp.Model("factory_planning")
    model.Params.OutputFlag = 0

    prod = model.addVars(products, months, lb=0.0, name="prod")
    inv = model.addVars(products, months, lb=0.0, name="inv")
    sales = model.addVars(products, months, lb=0.0, name="sales")

    revenue = gp.quicksum(profit[p] * sales[p, t] for p in products for t in months)
    holding = gp.quicksum(holding_cost * inv[p, t] for p in products for t in months)
    model.setObjective(revenue - holding, GRB.MAXIMIZE)

    # Month-0 balance (initial inventory is zero)
    for p in products:
        model.addConstr(
            prod[p, 0] == sales[p, 0] + inv[p, 0],
            name=f"balance_m0_p{p}",
        )

    # Months 1-3 balance
    for p in products:
        for t in range(1, 4):
            model.addConstr(
                inv[p, t - 1] + prod[p, t] == sales[p, t] + inv[p, t],
                name=f"balance_m{t}_p{p}",
            )

    # Machine capacity
    for mach in machine_names:
        for t in months:
            model.addConstr(
                gp.quicksum(proc_time[mach][p] * prod[p, t] for p in products)
                <= machine_hours[mach][t],
                name=f"cap_{mach}_m{t}",
            )

    # Inventory storage limits
    for p in products:
        for t in months:
            model.addConstr(inv[p, t] <= max_inv, name=f"invlim_p{p}_m{t}")

    # Sales limits
    for p in products:
        for t in months:
            model.addConstr(sales[p, t] <= sales_limits[p][t], name=f"saleslim_p{p}_m{t}")

    # Target inventory at end of horizon
    for p in products:
        model.addConstr(inv[p, 3] == target_inv[p], name=f"target_p{p}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}