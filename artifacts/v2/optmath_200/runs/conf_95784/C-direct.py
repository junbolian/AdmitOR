import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit0 = params["profit0"]
    profit1 = params["profit1"]
    hold_cost0 = params["hold_cost0"]
    hold_cost1 = params["hold_cost1"]
    inv_cap = params["inv_cap"]
    sales_max0 = params["sales_max0"]  # list of 4 values
    sales_max1 = params["sales_max1"]  # list of 4 values
    grinder_hours0 = params["grinder_hours0"]
    grinder_hours1 = params["grinder_hours1"]
    grinder_cap = params["grinder_cap"]  # list of 4 values
    drill_hours0 = params["drill_hours0"]
    drill_hours1 = params["drill_hours1"]
    drill_cap = params["drill_cap"]  # list of 4 values
    borer_hours0 = params["borer_hours0"]
    borer_hours1 = params["borer_hours1"]
    borer_cap = params["borer_cap"]  # list of 4 values
    final_inv_target = params["final_inv_target"]

    periods = range(4)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    prod0 = model.addVars(periods, lb=0, name="prod0")
    prod1 = model.addVars(periods, lb=0, name="prod1")
    inv0 = model.addVars(periods, lb=0, ub=inv_cap, name="inv0")
    inv1 = model.addVars(periods, lb=0, ub=inv_cap, name="inv1")
    sales0 = model.addVars(periods, lb=0, name="sales0")
    sales1 = model.addVars(periods, lb=0, name="sales1")

    # Objective: maximize profit - holding costs
    model.setObjective(
        gp.quicksum(profit0 * sales0[t] + profit1 * sales1[t]
                    - hold_cost0 * inv0[t] - hold_cost1 * inv1[t]
                    for t in periods),
        GRB.MAXIMIZE
    )

    # Inventory balance constraints
    # Period 0: production = sales + inventory
    model.addConstr(prod0[0] == sales0[0] + inv0[0], name="inv_bal0_p0")
    model.addConstr(prod1[0] == sales1[0] + inv1[0], name="inv_bal1_p0")

    # Periods 1-3: prev_inv + production = sales + inventory
    for t in range(1, 4):
        model.addConstr(inv0[t-1] + prod0[t] == sales0[t] + inv0[t], name=f"inv_bal0_p{t}")
        model.addConstr(inv1[t-1] + prod1[t] == sales1[t] + inv1[t], name=f"inv_bal1_p{t}")

    # Sales upper bounds
    for t in periods:
        model.addConstr(sales0[t] <= sales_max0[t], name=f"sales_max0_p{t}")
        model.addConstr(sales1[t] <= sales_max1[t], name=f"sales_max1_p{t}")

    # Machine capacity constraints
    for t in periods:
        model.addConstr(
            grinder_hours0 * prod0[t] + grinder_hours1 * prod1[t] <= grinder_cap[t],
            name=f"grinder_cap_p{t}"
        )
        model.addConstr(
            drill_hours0 * prod0[t] + drill_hours1 * prod1[t] <= drill_cap[t],
            name=f"drill_cap_p{t}"
        )
        model.addConstr(
            borer_hours0 * prod0[t] + borer_hours1 * prod1[t] <= borer_cap[t],
            name=f"borer_cap_p{t}"
        )

    # Final inventory target at end of Period 3
    model.addConstr(inv0[3] == final_inv_target, name="final_inv0")
    model.addConstr(inv1[3] == final_inv_target, name="final_inv1")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}