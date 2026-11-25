import gurobipy as gp
from gurobipy import GRB


def _per_product(val, p):
    """Return val[p] if val is a list/tuple, else val (scalar shared by all products)."""
    if isinstance(val, (list, tuple)):
        return val[p]
    return val


def solve(params):
    products = [0, 1]
    periods = [0, 1, 2, 3]
    # Machine types in order: grinders=0, drills=1, borers=2
    machine_indices = [0, 1, 2]

    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost"]
    machine_hours_per_unit = params["machine_hours_per_unit"]  # indexed [machine][product]
    capacities = [
        params["grinder_capacity"],
        params["drill_capacity"],
        params["borer_capacity"],
    ]
    inventory_limit = params["inventory_limit"]
    sales_limits = {
        0: params["sales_limit_product0"],
        1: params["sales_limit_product1"],
    }
    target_inventory = params["target_inventory"]

    model = gp.Model("factory_production_inventory")
    model.Params.OutputFlag = 0

    # Decision variables
    P = model.addVars(products, periods, name="Prod", lb=0)
    Inv = model.addVars(products, periods, name="Inv", lb=0)
    S = model.addVars(products, periods, name="Sales", lb=0)

    # Objective: maximize sales profit minus holding cost
    # holding_cost may be scalar or per-product; treat uniformly via _per_product
    model.setObjective(
        gp.quicksum(_per_product(profit_per_unit, p) * S[p, t]
                    for p in products for t in periods)
        - gp.quicksum(_per_product(holding_cost, p) * Inv[p, t]
                      for p in products for t in periods),
        GRB.MAXIMIZE,
    )

    # Initial balance (Period 0): production = sales + inventory
    for p in products:
        model.addConstr(P[p, 0] == S[p, 0] + Inv[p, 0], name=f"init_bal_{p}")

    # Inventory balance (Periods 1..3)
    for p in products:
        for t in periods[1:]:
            model.addConstr(
                Inv[p, t - 1] + P[p, t] == S[p, t] + Inv[p, t],
                name=f"inv_bal_{p}_{t}",
            )

    # Machine capacity: machine_hours_per_unit[m] is per-machine hours list/scalar over products
    for mi in machine_indices:
        hours = machine_hours_per_unit[mi]  # hours[p] or scalar
        cap = capacities[mi]               # cap[t]
        for t in periods:
            model.addConstr(
                gp.quicksum(_per_product(hours, p) * P[p, t] for p in products) <= cap[t],
                name=f"cap_m{mi}_{t}",
            )

    # Inventory limits and sales limits
    for p in products:
        for t in periods:
            model.addConstr(Inv[p, t] <= _per_product(inventory_limit, p),
                            name=f"inv_lim_{p}_{t}")
            model.addConstr(S[p, t] <= sales_limits[p][t], name=f"sales_lim_{p}_{t}")

    # Target inventory at end of Period 3 must be met exactly
    for p in products:
        model.addConstr(Inv[p, 3] == _per_product(target_inventory, p),
                        name=f"target_inv_{p}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": "failed"}