import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost_per_unit_per_period"]
    mh_grinder = params["machine_hours_grinder"]
    mh_drill = params["machine_hours_drill"]
    mh_borer = params["machine_hours_borer"]
    grinder_cap = params["grinder_capacity"]
    drill_cap = params["drill_capacity"]
    borer_cap = params["borer_capacity"]
    inv_limit = params["inventory_limit"]
    sales_limit = params["sales_limit"]
    target_inv = params["target_inventory"]

    periods = range(4)
    products = range(3)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    prod = model.addVars(periods, products, lb=0.0, name="prod")
    inv = model.addVars(periods, products, lb=0.0, name="inv")
    sales = model.addVars(periods, products, lb=0.0, name="sales")

    # Objective: maximize profit from sales minus holding costs
    model.setObjective(
        gp.quicksum(profit_per_unit[j] * sales[t, j] for t in periods for j in products)
        - gp.quicksum(holding_cost * inv[t, j] for t in periods for j in products),
        GRB.MAXIMIZE
    )

    # Initial balance (period 0): production = sales + inventory
    for j in products:
        model.addConstr(prod[0, j] == sales[0, j] + inv[0, j], name=f"init_bal_{j}")

    # Inventory balance (periods 1-3)
    for t in range(1, 4):
        for j in products:
            model.addConstr(
                inv[t - 1, j] + prod[t, j] == sales[t, j] + inv[t, j],
                name=f"inv_bal_{t}_{j}"
            )

    # Machine capacity constraints
    for t in periods:
        model.addConstr(
            gp.quicksum(mh_grinder[j] * prod[t, j] for j in products) <= grinder_cap[t],
            name=f"grinder_{t}"
        )
        model.addConstr(
            gp.quicksum(mh_drill[j] * prod[t, j] for j in products) <= drill_cap[t],
            name=f"drill_{t}"
        )
        model.addConstr(
            gp.quicksum(mh_borer[j] * prod[t, j] for j in products) <= borer_cap[t],
            name=f"borer_{t}"
        )

    # Inventory limits
    for t in periods:
        for j in products:
            model.addConstr(inv[t, j] <= inv_limit, name=f"inv_lim_{t}_{j}")

    # Sales limits
    for t in periods:
        for j in products:
            model.addConstr(sales[t, j] <= sales_limit[t][j], name=f"sales_lim_{t}_{j}")

    # Target inventory at end of period 3
    for j in products:
        model.addConstr(inv[3, j] == target_inv[j], name=f"target_inv_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}