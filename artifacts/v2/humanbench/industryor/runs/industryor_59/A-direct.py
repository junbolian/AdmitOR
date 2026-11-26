import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = ["I", "II", "III"]
    equip = ["A1", "A2", "B1", "B2", "B3"]

    # Allowed (product, equipment) pairs based on routing constraints
    allowed = {
        ("I", "A1"): True, ("I", "A2"): True,
        ("II", "A1"): True, ("II", "A2"): True,
        ("III", "A2"): True,
        ("I", "B1"): True, ("I", "B2"): True, ("I", "B3"): True,
        ("II", "B1"): True,
        ("III", "B2"): True,
    }

    upt = params["unit_processing_time"]  # list, order A1:I,II,III; A2:...; etc.
    avail = params["equipment_available_time"]
    cost_full = params["equipment_cost_full_load"]
    rm_cost = params["raw_material_cost"]
    price = params["unit_price"]

    # Map processing times: index over equip (5) x products (3)
    proc_time = {}
    for e_idx, e in enumerate(equip):
        for p_idx, p in enumerate(products):
            proc_time[(p, e)] = upt[e_idx * 3 + p_idx]

    avail_map = {e: avail[i] for i, e in enumerate(equip)}
    cost_map = {e: cost_full[i] for i, e in enumerate(equip)}
    rm_map = {p: rm_cost[i] for i, p in enumerate(products)}
    price_map = {p: price[i] for i, p in enumerate(products)}

    model = pyo.ConcreteModel()

    # Variables: quantity of product p processed on equipment e (for allowed pairs)
    pairs = [(p, e) for p in products for e in equip if allowed.get((p, e), False)]
    model.x = pyo.Var(pairs, domain=pyo.NonNegativeReals)

    # Equipment time constraints
    model.time_con = pyo.ConstraintList()
    for e in equip:
        relevant = [p for p in products if allowed.get((p, e), False)]
        if relevant:
            model.time_con.add(
                sum(proc_time[(p, e)] * model.x[(p, e)] for p in relevant)
                <= avail_map[e]
            )

    # Flow balance: total product p processed on its A step must equal total on its B step
    # For each product, the amount produced must be consistent across the two steps.
    # We treat the quantity of product p produced as the amount through A equipment,
    # and require that the amount through A equals the amount through B.
    model.balance = pyo.ConstraintList()
    for p in products:
        a_equip = [e for e in equip if e.startswith("A") and allowed.get((p, e), False)]
        b_equip = [e for e in equip if e.startswith("B") and allowed.get((p, e), False)]
        if a_equip and b_equip:
            model.balance.add(
                sum(model.x[(p, e)] for e in a_equip)
                == sum(model.x[(p, e)] for e in b_equip)
            )

    # Equipment utilization ratio variables to model cost at full load (proportional)
    # Cost scales linearly with utilization: cost_e * (time_used_e / available_e)
    # We can write cost directly as cost_e / avail_e * time_used_e
    # Revenue and material cost based on produced quantity (use A-step amounts)
    model.obj = pyo.Objective(
        expr=sum(
            (price_map[p] - rm_map[p])
            * sum(model.x[(p, e)] for e in equip if e.startswith("A") and allowed.get((p, e), False))
            for p in products
        )
        - sum(
            cost_map[e] / avail_map[e]
            * sum(proc_time[(p, e)] * model.x[(p, e)] for p in products if allowed.get((p, e), False))
            for e in equip
        ),
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}