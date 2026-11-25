import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_p0 = params["profit_per_unit_p0"]
    profit_p1 = params["profit_per_unit_p1"]
    holding_cost = params["holding_cost_per_unit_per_period"]
    grinder_cap = params["grinder_capacity_period"]
    drill_cap = params["drill_capacity_period"]
    borer_cap = params["borer_capacity_period"]
    grinder_p0 = params["grinder_hours_per_unit_p0"]
    grinder_p1 = params["grinder_hours_per_unit_p1"]
    drill_hours = params["drill_hours_per_unit"]
    borer_hours = params["borer_hours_per_unit"]
    max_inv = params["max_inventory_per_product_per_period"]
    max_sales_p0 = params["max_sales_p0_period"]
    max_sales_p1 = params["max_sales_p1_period"]
    final_inv_p0 = params["final_inventory_p0"]
    final_inv_p1 = params["final_inventory_p1"]

    periods = range(4)

    model = gp.Model("production_planning")
    model.setParam("OutputFlag", 0)

    # Decision variables
    produce_p0 = model.addVars(periods, lb=0.0, name="produce_p0")
    produce_p1 = model.addVars(periods, lb=0.0, name="produce_p1")
    sell_p0 = model.addVars(periods, lb=0.0, name="sell_p0")
    sell_p1 = model.addVars(periods, lb=0.0, name="sell_p1")
    inv_p0 = model.addVars(periods, lb=0.0, name="inv_p0")
    inv_p1 = model.addVars(periods, lb=0.0, name="inv_p1")

    # Objective: maximize profit from sales minus holding costs
    model.setObjective(
        gp.quicksum(profit_p0 * sell_p0[t] + profit_p1 * sell_p1[t]
                    - holding_cost * inv_p0[t] - holding_cost * inv_p1[t]
                    for t in periods),
        GRB.MAXIMIZE
    )

    # Inventory balance constraints
    for t in periods:
        if t == 0:
            model.addConstr(produce_p0[t] == sell_p0[t] + inv_p0[t], name=f"balance_p0_{t}")
            model.addConstr(produce_p1[t] == sell_p1[t] + inv_p1[t], name=f"balance_p1_{t}")
        else:
            model.addConstr(inv_p0[t-1] + produce_p0[t] == sell_p0[t] + inv_p0[t], name=f"balance_p0_{t}")
            model.addConstr(inv_p1[t-1] + produce_p1[t] == sell_p1[t] + inv_p1[t], name=f"balance_p1_{t}")

    # Machine capacity constraints
    for t in periods:
        model.addConstr(
            grinder_p0 * produce_p0[t] + grinder_p1 * produce_p1[t] <= grinder_cap[t],
            name=f"grinder_{t}"
        )
        model.addConstr(
            drill_hours * produce_p0[t] + drill_hours * produce_p1[t] <= drill_cap[t],
            name=f"drill_{t}"
        )
        model.addConstr(
            borer_hours * produce_p0[t] + borer_hours * produce_p1[t] <= borer_cap[t],
            name=f"borer_{t}"
        )

    # Inventory capacity constraints
    for t in periods:
        model.addConstr(inv_p0[t] <= max_inv, name=f"max_inv_p0_{t}")
        model.addConstr(inv_p1[t] <= max_inv, name=f"max_inv_p1_{t}")

    # Sales upper bound constraints
    for t in periods:
        model.addConstr(sell_p0[t] <= max_sales_p0[t], name=f"max_sales_p0_{t}")
        model.addConstr(sell_p1[t] <= max_sales_p1[t], name=f"max_sales_p1_{t}")

    # Final inventory requirements
    model.addConstr(inv_p0[3] == final_inv_p0, name="final_inv_p0")
    model.addConstr(inv_p1[3] == final_inv_p1, name="final_inv_p1")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}