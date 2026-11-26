import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]  # 3x4 matrix, demand[i][q]
    initial_inventory = params["initial_inventory"]  # list of 3
    final_inventory = params["final_inventory"]  # list of 3
    production_hours_per_quarter = params["production_hours_per_quarter"]
    unit_hours = params["unit_hours"]  # list of 3
    compensation_cost = params["compensation_cost"]  # list of 3
    storage_cost = params["storage_cost"]  # scalar or list; treat as per-unit per-quarter

    num_products = 3
    num_quarters = 4
    products = range(num_products)
    quarters = range(num_quarters)

    # storage_cost may be a scalar or list; normalize to per-product list
    if hasattr(storage_cost, '__len__'):
        sc = [storage_cost[i] for i in products]
    else:
        sc = [storage_cost for _ in products]

    model = gp.Model("production_planning")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # x[i][q]: production of product i in quarter q
    x = [[model.addVar(lb=0, name=f"x_{i}_{q}") for q in quarters] for i in products]

    # Product I cannot be produced in quarter 2 (index 1)
    model.addConstr(x[0][1] == 0, name="no_prod_I_q2")

    # inv[i][q]: inventory of product i at end of quarter q (after deliveries)
    # backlog[i][q]: backlog (late delivery) of product i at end of quarter q
    # We model inventory and backlog jointly:
    # At each quarter, we accumulate production, fulfill demand, carry inventory or backlog.
    #
    # Balance: inv[i][q] - backlog[i][q] = inv[i][q-1] - backlog[i][q-1] + x[i][q] - demand[i][q]
    # inv[i][q] >= 0, backlog[i][q] >= 0
    # At most one of inv or backlog is positive (complementarity not strictly needed for LP,
    # the objective drives them to not coexist).

    inv = [[model.addVar(lb=0, name=f"inv_{i}_{q}") for q in quarters] for i in products]
    backlog = [[model.addVar(lb=0, name=f"backlog_{i}_{q}") for q in quarters] for i in products]

    # Balance constraints
    for i in products:
        for q in quarters:
            prev_inv = initial_inventory[i] if q == 0 else inv[i][q-1]
            prev_backlog = 0.0 if q == 0 else backlog[i][q-1]
            model.addConstr(
                inv[i][q] - backlog[i][q] == prev_inv - prev_backlog + x[i][q] - demand[i][q],
                name=f"balance_{i}_{q}"
            )

    # Final inventory requirement
    for i in products:
        model.addConstr(inv[i][3] >= final_inventory[i], name=f"final_inv_{i}")
        model.addConstr(backlog[i][3] == 0, name=f"no_final_backlog_{i}")

    # Production hours constraint per quarter
    for q in quarters:
        model.addConstr(
            gp.quicksum(unit_hours[i] * x[i][q] for i in products) <= production_hours_per_quarter,
            name=f"hours_{q}"
        )

    # Objective: minimize total compensation (backlog cost) + storage cost
    obj = gp.quicksum(
        compensation_cost[i] * backlog[i][q] + sc[i] * inv[i][q]
        for i in products for q in quarters
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