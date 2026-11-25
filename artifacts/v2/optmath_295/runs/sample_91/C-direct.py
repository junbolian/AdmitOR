import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost_per_unit_month"]
    machine_hours_grinder = params["machine_hours_grinder"]
    machine_hours_drill = params["machine_hours_drill"]
    machine_hours_borer = params["machine_hours_borer"]
    machine_time_grinder = params["machine_time_grinder"]
    machine_time_drill = params["machine_time_drill"]
    machine_time_borer = params["machine_time_borer"]
    max_inventory = params["max_inventory"]
    sales_limit = params["sales_limit"]
    target_final_inventory = params["target_final_inventory"]

    products = [0, 1, 2]
    months = [0, 1, 2, 3]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    produce = model.addVars(products, months, lb=0.0, name="produce")
    inventory = model.addVars(products, months, lb=0.0, name="inventory")
    sell = model.addVars(products, months, lb=0.0, name="sell")

    model.setObjective(
        gp.quicksum(profit_per_unit[p] * sell[p, t] for p in products for t in months)
        - gp.quicksum(holding_cost * inventory[p, t] for p in products for t in months),
        GRB.MAXIMIZE
    )

    for p in products:
        model.addConstr(produce[p, 0] == sell[p, 0] + inventory[p, 0], name=f"balance_p{p}_m0")
        for t in months[1:]:
            model.addConstr(
                inventory[p, t-1] + produce[p, t] == sell[p, t] + inventory[p, t],
                name=f"balance_p{p}_m{t}"
            )

    for t in months:
        model.addConstr(
            gp.quicksum(machine_time_grinder[p] * produce[p, t] for p in products)
            <= machine_hours_grinder[t],
            name=f"grinder_m{t}"
        )
        model.addConstr(
            gp.quicksum(machine_time_drill[p] * produce[p, t] for p in products)
            <= machine_hours_drill[t],
            name=f"drill_m{t}"
        )
        model.addConstr(
            gp.quicksum(machine_time_borer[p] * produce[p, t] for p in products)
            <= machine_hours_borer[t],
            name=f"borer_m{t}"
        )

    # max_inventory may be a scalar or a per-product sequence; handle both
    for p in products:
        try:
            inv_cap = max_inventory[p]
        except (TypeError, KeyError):
            inv_cap = max_inventory
        for t in months:
            model.addConstr(inventory[p, t] <= inv_cap, name=f"inv_cap_p{p}_m{t}")

    for p in products:
        for t in months:
            model.addConstr(sell[p, t] <= sales_limit[p][t], name=f"sales_cap_p{p}_m{t}")

    for p in products:
        try:
            final_inv = target_final_inventory[p]
        except (TypeError, KeyError):
            final_inv = target_final_inventory
        model.addConstr(inventory[p, 3] == final_inv, name=f"final_inv_p{p}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}