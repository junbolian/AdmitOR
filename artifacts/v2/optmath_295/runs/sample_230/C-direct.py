import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost"]
    grinder_hours = params["grinder_hours"]
    drill_hours = params["drill_hours"]
    borer_hours = params["borer_hours"]
    max_inventory = params["max_inventory"]
    max_sales = params["max_sales"]
    final_inventory = params["final_inventory"]

    P = 3
    T = 6

    # --- Locate machine-hours-per-unit data (key name may vary across harnesses) ---
    machine_hours_per_unit = None
    for key in (
        "machine_hours_per_unit",
        "machine_hours",
        "unit_machine_hours",
        "hours_per_unit",
        "machine_time_per_unit",
        "machine_times_per_unit",
        "machine_hours_per_units",
        "machine_hour_per_unit",
        "processing_times",
        "processing_time",
    ):
        if key in params:
            machine_hours_per_unit = params[key]
            break

    if machine_hours_per_unit is None:
        # Try per-machine-type keys with various naming patterns
        _suffixes = (
            "_hours_per_unit",
            "_unit_hours",
            "_time_per_unit",
            "_processing_time",
        )
        per_machine_vals = []
        all_found = True
        for prefix in ("grinder", "drill", "borer"):
            found = False
            for suffix in _suffixes:
                k = prefix + suffix
                if k in params:
                    per_machine_vals.append(params[k])
                    found = True
                    break
            if not found:
                all_found = False
                break
        if all_found and len(per_machine_vals) == 3:
            machine_hours_per_unit = [
                [per_machine_vals[0][p], per_machine_vals[1][p], per_machine_vals[2][p]]
                for p in range(P)
            ]

    if machine_hours_per_unit is None:
        raise KeyError(
            "Cannot find machine-hours-per-unit data. Available keys: "
            + ", ".join(sorted(params.keys()))
        )

    # Normalise dict format to list-of-lists [product][machine_type]
    if isinstance(machine_hours_per_unit, dict):
        if "grinder" in machine_hours_per_unit:
            gh = machine_hours_per_unit["grinder"]
            dh = machine_hours_per_unit["drill"]
            bh = machine_hours_per_unit["borer"]
            machine_hours_per_unit = [[gh[p], dh[p], bh[p]] for p in range(P)]
        elif (0, 0) in machine_hours_per_unit:
            machine_hours_per_unit = [
                [machine_hours_per_unit[(p, m)] for m in range(3)]
                for p in range(P)
            ]

    # --- Normalise scalar / list params ---
    if isinstance(final_inventory, (int, float)):
        final_inv = [final_inventory] * P
    else:
        final_inv = list(final_inventory)

    if isinstance(max_inventory, (list, tuple)):
        max_inv = list(max_inventory)
    else:
        max_inv = [max_inventory] * P

    # --- Build model ---
    model = gp.Model("production_planning")
    model.setParam("OutputFlag", 0)

    produce = model.addVars(P, T, lb=0, vtype=GRB.CONTINUOUS, name="produce")
    inv = model.addVars(P, T, lb=0, vtype=GRB.CONTINUOUS, name="inv")
    sell = model.addVars(P, T, lb=0, vtype=GRB.CONTINUOUS, name="sell")

    revenue = gp.quicksum(
        profit_per_unit[p] * sell[p, t] for p in range(P) for t in range(T)
    )
    holding = holding_cost * gp.quicksum(
        inv[p, t] for p in range(P) for t in range(T)
    )
    model.setObjective(revenue - holding, GRB.MAXIMIZE)

    # Period 0 balance (initial inventory = 0)
    for p in range(P):
        model.addConstr(produce[p, 0] == sell[p, 0] + inv[p, 0])

    # Periods 1-5 balance
    for p in range(P):
        for t in range(1, T):
            model.addConstr(inv[p, t - 1] + produce[p, t] == sell[p, t] + inv[p, t])

    # Machine capacity: grinder=0, drill=1, borer=2
    for t in range(T):
        model.addConstr(
            gp.quicksum(machine_hours_per_unit[p][0] * produce[p, t] for p in range(P))
            <= grinder_hours[t]
        )
        model.addConstr(
            gp.quicksum(machine_hours_per_unit[p][1] * produce[p, t] for p in range(P))
            <= drill_hours[t]
        )
        model.addConstr(
            gp.quicksum(machine_hours_per_unit[p][2] * produce[p, t] for p in range(P))
            <= borer_hours[t]
        )

    # Inventory capacity
    for p in range(P):
        for t in range(T):
            model.addConstr(inv[p, t] <= max_inv[p])

    # Sales upper bounds
    for p in range(P):
        for t in range(T):
            model.addConstr(sell[p, t] <= max_sales[p][t])

    # Final inventory requirement
    for p in range(P):
        model.addConstr(inv[p, T - 1] == final_inv[p])

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status in (GRB.INFEASIBLE, GRB.INF_OR_UNBD):
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "failed"}