import gurobipy as gp
from gurobipy import GRB

def solve(params):
    revenue = [
        params["revenue_product_0"],
        params["revenue_product_1"],
        params["revenue_product_2"],
    ]
    holding_cost = params["holding_cost"]

    grinder_cap = [
        params["grinder_capacity_period_0"],
        params["grinder_capacity_periods_1_3"],
        params["grinder_capacity_periods_1_3"],
        params["grinder_capacity_periods_1_3"],
    ]
    drill_cap = [
        params["drill_capacity_periods_0_1_3"],
        params["drill_capacity_periods_0_1_3"],
        params["drill_capacity_period_2"],
        params["drill_capacity_periods_0_1_3"],
    ]
    borer_cap = [params["borer_capacity_all_periods"]] * 4

    max_inv = params["max_inventory_per_product_per_period"]

    sales_limits = [
        params["sales_limit_p0"],
        params["sales_limit_p1"],
        params["sales_limit_p2"],
        params["sales_limit_p3"],
    ]

    final_inv_req = params["final_inventory_required"]

    # Machine hours per unit: structural constants from problem description
    # grinder: product_0=4, product_1=2, product_2=3
    # drill:   product_0=2, product_1=3, product_2=2
    # borer:   product_0=2, product_1=2, product_2=2 (stated in problem)
    grinder_hours = [4, 2, 3]
    drill_hours   = [2, 3, 2]
    borer_hours   = [2, 2, 2]

    products = range(3)
    periods  = range(4)

    model = gp.Model("factory_planning")
    model.setParam("OutputFlag", 0)

    # Decision variables
    produce = model.addVars(products, periods, lb=0.0, name="produce")
    store   = model.addVars(products, periods, lb=0.0, name="store")
    sell    = model.addVars(products, periods, lb=0.0, name="sell")

    # Objective: maximize revenue - holding costs
    model.setObjective(
        gp.quicksum(revenue[p] * sell[p, t] for p in products for t in periods)
        - gp.quicksum(holding_cost * store[p, t] for p in products for t in periods),
        GRB.MAXIMIZE,
    )

    # Inventory balance constraints
    for p in products:
        for t in periods:
            if t == 0:
                model.addConstr(
                    produce[p, t] == sell[p, t] + store[p, t],
                    name=f"balance_p{p}_t{t}",
                )
            else:
                model.addConstr(
                    store[p, t - 1] + produce[p, t] == sell[p, t] + store[p, t],
                    name=f"balance_p{p}_t{t}",
                )

    # Machine capacity constraints
    for t in periods:
        model.addConstr(
            gp.quicksum(grinder_hours[p] * produce[p, t] for p in products) <= grinder_cap[t],
            name=f"grinder_t{t}",
        )
        model.addConstr(
            gp.quicksum(drill_hours[p] * produce[p, t] for p in products) <= drill_cap[t],
            name=f"drill_t{t}",
        )
        model.addConstr(
            gp.quicksum(borer_hours[p] * produce[p, t] for p in products) <= borer_cap[t],
            name=f"borer_t{t}",
        )

    # Inventory capacity constraints
    for p in products:
        for t in periods:
            model.addConstr(store[p, t] <= max_inv, name=f"inv_cap_p{p}_t{t}")

    # Sales limit constraints
    for t in periods:
        lim = sales_limits[t]
        for p in products:
            model.addConstr(sell[p, t] <= lim[p], name=f"sales_p{p}_t{t}")

    # Final inventory requirement
    for p in products:
        model.addConstr(store[p, 3] == final_inv_req, name=f"final_inv_p{p}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}