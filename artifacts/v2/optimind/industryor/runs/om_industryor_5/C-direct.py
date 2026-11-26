import gurobipy as gp
from gurobipy import GRB

def solve(params):
    reservations = params["reservations"]                    # shape (3, 4)
    ending_inv_req = params["ending_inventory_required"]     # scalar or length-3 list
    prod_hours_per_q = params["production_hours_per_quarter"]  # scalar
    hours_per_unit = params["hours_per_unit"]                # length 3
    delay_penalty = params["delay_penalty"]                  # length 3
    inventory_cost = params["inventory_cost"]                # scalar or length 3

    I = 3   # products: 0=I, 1=II, 2=III
    Q = 4   # quarters: 0..3

    # Normalize ending_inv_req to a list of length I
    if hasattr(ending_inv_req, '__len__'):
        end_req = [ending_inv_req[i] for i in range(I)]
    else:
        end_req = [ending_inv_req] * I

    # Normalize inventory_cost to a list of length I
    if hasattr(inventory_cost, '__len__'):
        inv_cost = [inventory_cost[i] for i in range(I)]
    else:
        inv_cost = [inventory_cost] * I

    model = gp.Model("production_scheduling")
    model.setParam("OutputFlag", 0)

    # x[i, q] = units of product i produced in quarter q
    x = model.addVars(I, Q, lb=0.0, name="x")

    # Product I (index 0) cannot be produced in quarter 2 (index 1)
    model.addConstr(x[0, 1] == 0, name="no_prod_I_Q2")

    # Production hours constraint per quarter
    for q in range(Q):
        model.addConstr(
            gp.quicksum(hours_per_unit[i] * x[i, q] for i in range(I)) <= prod_hours_per_q,
            name=f"hours_q{q}"
        )

    # inv[i,q]: finished goods inventory at end of quarter q (produced but undelivered)
    # back[i,q]: backlog (unmet demand) at end of quarter q
    # Net stock balance: inv[i,q] - back[i,q] = inv[i,q-1] - back[i,q-1] + x[i,q] - demand[i,q]
    # The optimizer naturally avoids simultaneous positive inv and back due to cost penalties.

    inv = model.addVars(I, Q, lb=0.0, name="inv")
    back = model.addVars(I, Q, lb=0.0, name="back")

    for i in range(I):
        for q in range(Q):
            dem = reservations[i][q]
            if q == 0:
                prev_inv = 0.0
                prev_back = 0.0
            else:
                prev_inv = inv[i, q - 1]
                prev_back = back[i, q - 1]
            model.addConstr(
                inv[i, q] - back[i, q] == prev_inv - prev_back + x[i, q] - dem,
                name=f"balance_i{i}_q{q}"
            )

    # Ending inventory requirement: inventory at end of Q4 >= required, no backlog
    for i in range(I):
        model.addConstr(inv[i, Q - 1] >= end_req[i], name=f"end_inv_i{i}")
        model.addConstr(back[i, Q - 1] == 0, name=f"end_back_i{i}")

    # Objective: inventory holding cost + delay penalty cost
    # Each unit of inventory held for a quarter costs inv_cost[i].
    # Each unit of backlog held for a quarter costs delay_penalty[i] (1 quarter of delay).
    obj = gp.quicksum(
        inv_cost[i] * inv[i, q] + delay_penalty[i] * back[i, q]
        for i in range(I)
        for q in range(Q)
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