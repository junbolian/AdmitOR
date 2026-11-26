import gurobipy as gp
from gurobipy import GRB

def solve(params):
    production_hours_per_quarter = params["production_hours_per_quarter"]
    hours_I = params["hours_per_unit_I"]
    hours_II = params["hours_per_unit_II"]
    hours_III = params["hours_per_unit_III"]
    orders_I = params["orders_I"]   # list of 4 values
    orders_II = params["orders_II"]
    orders_III = params["orders_III"]
    ending_inv_required = params["ending_inventory_required"]
    comp_I_II = params["compensation_per_unit_per_quarter_I_II"]
    comp_III = params["compensation_per_unit_per_quarter_III"]
    storage_fee = params["storage_fee_per_unit_per_quarter"]

    quarters = range(4)  # 0..3
    products = range(3)  # 0=I, 1=II, 2=III

    orders = [orders_I, orders_II, orders_III]
    hours = [hours_I, hours_II, hours_III]
    comp = [comp_I_II, comp_I_II, comp_III]

    model = gp.Model("production_planning")
    model.setParam("OutputFlag", 0)

    # x[p][q] = units of product p produced in quarter q
    x = [[model.addVar(lb=0, name=f"x_{p}_{q}") for q in quarters] for p in products]

    # Product I cannot be produced in quarter 2 (index 1)
    model.addConstr(x[0][1] == 0, name="no_prod_I_q2")

    # Production capacity constraints
    for q in quarters:
        model.addConstr(
            gp.quicksum(hours[p] * x[p][q] for p in products) <= production_hours_per_quarter,
            name=f"capacity_q{q}"
        )

    # Inventory tracking
    # inv[p][q] = inventory of product p at END of quarter q (after production, before/after delivery)
    # We model cumulative: at end of quarter q,
    #   cumulative_produced[p][q] = sum of x[p][0..q]
    #   cumulative_ordered[p][q] = sum of orders[p][0..q]
    # 
    # Delivery model: orders must eventually be delivered.
    # d[p][q] = units of product p delivered in quarter q
    # d[p][q] >= 0
    # sum over q' <= q of d[p][q'] >= orders[p][0] + ... + orders[p][q]  (all orders up to q must be met by end)
    # Actually, late delivery means we pay compensation per unit per quarter delayed.
    # 
    # Let's define:
    #   late[p][q] = units of product p whose order in quarter q is delivered late (after quarter q)
    #   stored[p][q] = units produced but not yet delivered at end of quarter q
    #
    # Alternative: use cumulative production vs cumulative demand approach.
    # 
    # Let CP[p][q] = cumulative production of p through quarter q
    # Let CD[p][q] = cumulative orders of p through quarter q
    # 
    # Inventory at end of quarter q = CP[p][q] - actual cumulative deliveries through q
    # For compensation: if order in quarter q is not fully delivered by quarter q,
    #   the undelivered portion in quarter t (t > q) incurs comp per unit per quarter.
    #
    # Let undelivered[p][q] = units of order[p][q] still undelivered at the end of quarter q
    # Then at end of quarter q+1, undelivered[p][q] becomes undelivered after q+1.
    # This requires tracking per-order delivery.
    #
    # Simpler approach: 
    # Let backlog[p][q] = total units of product p that have been ordered by end of quarter q
    #                     but not yet delivered by end of quarter q (= cumulative orders - cumulative deliveries)
    # compensation cost = comp[p] * backlog[p][q] per quarter (backlog carried into next quarter)
    # storage cost = storage_fee * inventory[p][q] per quarter
    # 
    # inventory[p][q] = CP[p][q] - CD[p][q] + backlog[p][q]  (units on hand = produced - net delivered)
    # Actually: delivered[p][q] = min(available, ordered) decisions
    #
    # Let's define:
    #   inv[p][q] = on-hand inventory at end of quarter q (non-negative)
    #   bl[p][q]  = backlog at end of quarter q (non-negative)
    #   inv[p][q] - bl[p][q] = CP[p][q] - CD[p][q]
    #   inv[p][q] * bl[p][q] = 0  (complementarity - but Gurobi needs linearization or we can note
    #                               that optimality will enforce it since both have positive costs)
    #
    # Since both storage and backlog incur costs, at optimum they won't both be positive simultaneously.

    inv = [[model.addVar(lb=0, name=f"inv_{p}_{q}") for q in quarters] for p in products]
    bl  = [[model.addVar(lb=0, name=f"bl_{p}_{q}")  for q in quarters] for p in products]

    # Cumulative orders
    cum_orders = [[sum(orders[p][:q+1]) for q in quarters] for p in products]

    # Inventory and backlog balance:
    # At end of quarter q:
    #   inv[p][q] - bl[p][q] = sum(x[p][0..q]) - cum_orders[p][q]
    # At end of quarter 4 (q=3): inv[p][3] >= ending_inv_required, bl[p][3] = 0

    for p in products:
        for q in quarters:
            cum_prod = gp.quicksum(x[p][qq] for qq in range(q+1))
            model.addConstr(
                inv[p][q] - bl[p][q] == cum_prod - cum_orders[p][q],
                name=f"balance_{p}_{q}"
            )

    # End of quarter 4: backlog must be 0, inventory >= required
    for p in products:
        model.addConstr(bl[p][3] == 0, name=f"no_backlog_end_{p}")
        model.addConstr(inv[p][3] >= ending_inv_required, name=f"ending_inv_{p}")

    # Objective: minimize total compensation + storage
    # Compensation: backlog[p][q] * comp[p] (backlog at end of quarter q means those units
    #   were late by at least 1 quarter, costing comp per unit per quarter)
    # Storage: inv[p][q] * storage_fee (inventory on hand at end of quarter q costs storage)
    
    obj = gp.quicksum(
        comp[p] * bl[p][q] + storage_fee * inv[p][q]
        for p in products for q in quarters
    )
    model.setObjective(obj, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}