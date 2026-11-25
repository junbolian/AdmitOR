import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit = [params["profit_product0"], params["profit_product1"]]
    holding_cost = params["holding_cost"]
    grinder_cap = params["grinder_capacity"]
    drill_cap = params["drill_capacity"]
    borer_cap = params["borer_capacity"]
    time_grinder = [params["time_product0_grinder"], params["time_product1_grinder"]]
    time_drill = [params["time_product0_drill"], params["time_product1_drill"]]
    time_borer = [params["time_product0_borer"], params["time_product1_borer"]]
    inv_limit = params["inventory_limit"]
    sales_limit = [params["sales_limit_product0"], params["sales_limit_product1"]]
    target_inv = params["target_inventory"]

    products = [0, 1]
    periods = [0, 1, 2, 3]

    # sales_limit is expected as a list of 4 values per product
    # but params stores them as single values per period — need to handle list or scalar
    # Based on problem description, sales_limit_product0 and sales_limit_product1
    # are per-period arrays. We'll treat them as lists indexed by period.

    model = gp.Model("factory_planning")
    model.setParam("OutputFlag", 0)

    # Decision variables
    prod = model.addVars(products, periods, lb=0.0, name="prod")
    inv = model.addVars(products, periods, lb=0.0, ub=inv_limit, name="inv")
    sales = model.addVars(products, periods, lb=0.0, name="sales")

    # Objective: maximize profit from sales minus holding costs
    model.setObjective(
        gp.quicksum(profit[p] * sales[p, t] for p in products for t in periods)
        - gp.quicksum(holding_cost * inv[p, t] for p in products for t in periods),
        GRB.MAXIMIZE
    )

    # Inventory balance constraints
    for p in products:
        # Period 0: production = sales + inventory
        model.addConstr(prod[p, 0] == sales[p, 0] + inv[p, 0], name=f"balance_{p}_0")
        # Periods 1-3: prev_inv + production = sales + inventory
        for t in [1, 2, 3]:
            model.addConstr(
                inv[p, t-1] + prod[p, t] == sales[p, t] + inv[p, t],
                name=f"balance_{p}_{t}"
            )

    # Machine capacity constraints
    for t in periods:
        model.addConstr(
            gp.quicksum(time_grinder[p] * prod[p, t] for p in products) <= grinder_cap,
            name=f"grinder_{t}"
        )
        model.addConstr(
            gp.quicksum(time_drill[p] * prod[p, t] for p in products) <= drill_cap,
            name=f"drill_{t}"
        )
        model.addConstr(
            gp.quicksum(time_borer[p] * prod[p, t] for p in products) <= borer_cap,
            name=f"borer_{t}"
        )

    # Sales limits
    for p in products:
        sl = sales_limit[p]
        for t in periods:
            model.addConstr(sales[p, t] <= sl[t], name=f"sales_limit_{p}_{t}")

    # Target inventory at end of horizon (period 3)
    for p in products:
        model.addConstr(inv[p, 3] == target_inv, name=f"target_inv_{p}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}