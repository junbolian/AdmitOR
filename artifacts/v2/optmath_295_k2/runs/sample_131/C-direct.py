import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_vals = [
        float(params["profit_product_0"]),
        float(params["profit_product_1"]),
        float(params["profit_product_2"]),
    ]
    holding_cost = float(params["holding_cost"])
    grinder_cap = float(params["grinder_capacity"])
    drill_cap = float(params["drill_capacity"])
    borer_cap = float(params["borer_capacity"])
    max_inv = float(params["max_inventory"])
    final_target = float(params["final_inventory_target"])

    max_sales = {}
    for t in range(4):
        for p in range(3):
            max_sales[(t, p)] = float(params[f"max_sales_period_{t}_product_{p}"])

    time_grinder = [
        float(params["time_grinder_product_0"]),
        float(params["time_grinder_product_1"]),
        float(params["time_grinder_product_2"]),
    ]
    time_drill = [
        float(params["time_drill_product_0"]),
        float(params["time_drill_product_1"]),
        float(params["time_drill_product_2"]),
    ]
    time_borer = [
        float(params["time_borer_product_0"]),
        float(params["time_borer_product_1"]),
        float(params["time_borer_product_2"]),
    ]

    periods = range(4)
    products = range(3)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    produce = model.addVars(periods, products, lb=0.0, name="produce")
    inventory = model.addVars(
        periods, products, lb=0.0,
        ub={(t, p): max_inv for t in periods for p in products},
        name="inventory",
    )
    sell = model.addVars(
        periods, products, lb=0.0,
        ub={(t, p): max_sales[(t, p)] for t in periods for p in products},
        name="sell",
    )

    # Objective: maximize profit minus holding costs
    revenue = gp.quicksum(
        profit_vals[p] * sell[t, p] for t in periods for p in products
    )
    holding = gp.quicksum(
        holding_cost * inventory[t, p] for t in periods for p in products
    )
    model.setObjective(revenue - holding, GRB.MAXIMIZE)

    # Inventory balance constraints
    for p in products:
        model.addConstr(
            produce[0, p] == sell[0, p] + inventory[0, p],
            name=f"balance_0_{p}",
        )
        for t in range(1, 4):
            model.addConstr(
                inventory[t - 1, p] + produce[t, p] == sell[t, p] + inventory[t, p],
                name=f"balance_{t}_{p}",
            )

    # Final inventory target
    for p in products:
        model.addConstr(inventory[3, p] == final_target, name=f"final_inv_{p}")

    # Machine capacity constraints
    for t in periods:
        model.addConstr(
            gp.quicksum(time_grinder[p] * produce[t, p] for p in products) <= grinder_cap,
            name=f"grinder_{t}",
        )
        model.addConstr(
            gp.quicksum(time_drill[p] * produce[t, p] for p in products) <= drill_cap,
            name=f"drill_{t}",
        )
        borer_avail = 0.0 if t == 2 else borer_cap
        model.addConstr(
            gp.quicksum(time_borer[p] * produce[t, p] for p in products) <= borer_avail,
            name=f"borer_{t}",
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}