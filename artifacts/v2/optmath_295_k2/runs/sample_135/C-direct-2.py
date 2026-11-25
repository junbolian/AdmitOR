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

    # Variables
    produce = {}
    sell = {}
    inventory = {}

    for t in periods:
        produce[0, t] = model.addVar(lb=0, name=f"produce_p0_t{t}")
        produce[1, t] = model.addVar(lb=0, name=f"produce_p1_t{t}")
        sell[0, t] = model.addVar(lb=0, name=f"sell_p0_t{t}")
        sell[1, t] = model.addVar(lb=0, name=f"sell_p1_t{t}")
        inventory[0, t] = model.addVar(lb=0, ub=max_inv, name=f"inv_p0_t{t}")
        inventory[1, t] = model.addVar(lb=0, ub=max_inv, name=f"inv_p1_t{t}")

    # Objective: maximize profit from sales minus holding costs
    revenue = gp.quicksum(
        profit_p0 * sell[0, t] + profit_p1 * sell[1, t] for t in periods
    )
    holding = gp.quicksum(
        holding_cost * (inventory[0, t] + inventory[1, t]) for t in periods
    )
    model.setObjective(revenue - holding, GRB.MAXIMIZE)

    # Inventory balance constraints
    for p, final_inv in [(0, final_inv_p0), (1, final_inv_p1)]:
        for t in periods:
            if t == 0:
                # Period 0: production = sales + inventory
                model.addConstr(
                    produce[p, 0] == sell[p, 0] + inventory[p, 0],
                    name=f"balance_p{p}_t0"
                )
            else:
                # Period t: prev_inventory + production = sales + inventory
                model.addConstr(
                    inventory[p, t - 1] + produce[p, t] == sell[p, t] + inventory[p, t],
                    name=f"balance_p{p}_t{t}"
                )

        # Final inventory requirement
        model.addConstr(inventory[p, 3] == final_inv, name=f"final_inv_p{p}")

    # Sales upper bounds
    for t in periods:
        model.addConstr(sell[0, t] <= max_sales_p0[t], name=f"max_sales_p0_t{t}")
        model.addConstr(sell[1, t] <= max_sales_p1[t], name=f"max_sales_p1_t{t}")

    # Machine capacity constraints
    for t in periods:
        model.addConstr(
            grinder_p0 * produce[0, t] + grinder_p1 * produce[1, t] <= grinder_cap[t],
            name=f"grinder_t{t}"
        )
        model.addConstr(
            drill_hours * produce[0, t] + drill_hours * produce[1, t] <= drill_cap[t],
            name=f"drill_t{t}"
        )
        model.addConstr(
            borer_hours * produce[0, t] + borer_hours * produce[1, t] <= borer_cap[t],
            name=f"borer_t{t}"
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