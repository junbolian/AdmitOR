import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit0 = params["profit_per_unit_product0"]
    profit1 = params["profit_per_unit_product1"]
    holding_cost = params["holding_cost_per_unit_per_period"]

    grinder_h0 = params["grinder_hours_product0"]
    grinder_h1 = params["grinder_hours_product1"]
    grinder_cap = params["grinder_capacity_per_period"]

    drill_h0 = params["drill_hours_product0"]
    drill_h1 = params["drill_hours_product1"]
    drill_cap = params["drill_capacity_per_period"]

    borer_h0 = params["borer_hours_product0"]
    borer_h1 = params["borer_hours_product1"]
    borer_cap = params["borer_capacity_per_period"]

    max_inv0 = params["max_inventory_product0"]
    max_inv1 = params["max_inventory_product1"]

    sales_lim0 = params["sales_limit_product0"]   # list of 4 values
    sales_lim1 = params["sales_limit_product1"]   # list of 4 values

    target_inv0 = params["target_inventory_product0"]
    target_inv1 = params["target_inventory_product1"]

    T = 4  # periods 0..3
    periods = range(T)

    model = gp.Model("factory")
    model.setParam("OutputFlag", 0)

    # Decision variables
    prod0 = model.addVars(T, lb=0.0, name="prod0")
    prod1 = model.addVars(T, lb=0.0, name="prod1")
    inv0  = model.addVars(T, lb=0.0, ub=max_inv0, name="inv0")
    inv1  = model.addVars(T, lb=0.0, ub=max_inv1, name="inv1")
    sales0 = model.addVars(T, lb=0.0, name="sales0")
    sales1 = model.addVars(T, lb=0.0, name="sales1")

    # Objective: maximize profit from sales minus holding costs
    model.setObjective(
        gp.quicksum(profit0 * sales0[t] + profit1 * sales1[t]
                    - holding_cost * inv0[t] - holding_cost * inv1[t]
                    for t in periods),
        GRB.MAXIMIZE
    )

    # Inventory balance constraints
    for t in periods:
        if t == 0:
            # Initial balance: no starting inventory
            model.addConstr(prod0[t] == sales0[t] + inv0[t], name=f"bal0_t{t}")
            model.addConstr(prod1[t] == sales1[t] + inv1[t], name=f"bal1_t{t}")
        else:
            model.addConstr(inv0[t-1] + prod0[t] == sales0[t] + inv0[t], name=f"bal0_t{t}")
            model.addConstr(inv1[t-1] + prod1[t] == sales1[t] + inv1[t], name=f"bal1_t{t}")

    # Machine capacity constraints
    for t in periods:
        model.addConstr(
            grinder_h0 * prod0[t] + grinder_h1 * prod1[t] <= grinder_cap,
            name=f"grinder_t{t}"
        )
        model.addConstr(
            drill_h0 * prod0[t] + drill_h1 * prod1[t] <= drill_cap,
            name=f"drill_t{t}"
        )
        model.addConstr(
            borer_h0 * prod0[t] + borer_h1 * prod1[t] <= borer_cap,
            name=f"borer_t{t}"
        )

    # Sales limits
    for t in periods:
        model.addConstr(sales0[t] <= sales_lim0[t], name=f"slim0_t{t}")
        model.addConstr(sales1[t] <= sales_lim1[t], name=f"slim1_t{t}")

    # Terminal inventory targets
    model.addConstr(inv0[T-1] == target_inv0, name="term_inv0")
    model.addConstr(inv1[T-1] == target_inv1, name="term_inv1")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}