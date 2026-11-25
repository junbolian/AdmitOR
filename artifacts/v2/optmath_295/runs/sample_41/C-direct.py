import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_unit_sold = params["profit_per_unit_sold"]
    inventory_holding_cost = params["inventory_holding_cost"]
    machine_hours_per_unit = params["machine_hours_per_unit"]
    machine_capacity_per_period = params["machine_capacity_per_period"]
    inventory_capacity_per_product = params["inventory_capacity_per_product"]
    sales_limit = params["sales_limit"]
    target_final_inventory = params["target_final_inventory"]

    products = range(3)
    periods = range(4)
    machines = range(3)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    produce = model.addVars(products, periods, lb=0.0, name="produce")
    inventory = model.addVars(products, periods, lb=0.0, name="inventory")
    sell = model.addVars(products, periods, lb=0.0, name="sell")

    model.setObjective(
        gp.quicksum(profit_per_unit_sold[p] * sell[p, t] for p in products for t in periods)
        - gp.quicksum(inventory_holding_cost * inventory[p, t] for p in products for t in periods),
        GRB.MAXIMIZE
    )

    # Inventory balance: period 0
    for p in products:
        model.addConstr(produce[p, 0] == sell[p, 0] + inventory[p, 0], name=f"balance_init_{p}")

    # Inventory balance: periods 1-3
    for p in products:
        for t in range(1, 4):
            model.addConstr(
                inventory[p, t - 1] + produce[p, t] == sell[p, t] + inventory[p, t],
                name=f"balance_{p}_{t}"
            )

    # Machine capacity constraints
    for mach in machines:
        for t in periods:
            model.addConstr(
                gp.quicksum(machine_hours_per_unit[mach][p] * produce[p, t] for p in products)
                <= machine_capacity_per_period[mach],
                name=f"machine_{mach}_{t}"
            )

    # Inventory capacity constraints — capacity may be a scalar or a per-product sequence
    for p in products:
        for t in periods:
            try:
                cap = inventory_capacity_per_product[p]
            except TypeError:
                cap = inventory_capacity_per_product
            model.addConstr(inventory[p, t] <= cap, name=f"inv_cap_{p}_{t}")

    # Sales limit constraints
    for p in products:
        for t in periods:
            model.addConstr(sell[p, t] <= sales_limit[p][t], name=f"sales_lim_{p}_{t}")

    # Target final inventory
    for p in products:
        try:
            tgt = target_final_inventory[p]
        except TypeError:
            tgt = target_final_inventory
        model.addConstr(inventory[p, 3] == tgt, name=f"final_inv_{p}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}