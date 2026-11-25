# IR: {"sets":{"S":"range(num_slots)","B":"range(num_brands)","E":"adjacency_links","A":"{(s,b): s in S, b in allowed_brands_per_slot[s]}","C":"{(u,v,b): (u,v) in E, (u,b) in A, (v,b) in A}"},"params":["num_slots","num_brands","adjacency_links","allowed_brands_per_slot"],"variables":{"x[s,b]":"Binary for (s,b) in A","highest_brand":"NonnegativeInteger"},"constraints":["sum(x[s,b] for b with (s,b) in A) == 1 for each s in S","x[u,b] + x[v,b] <= 1 for each (u,v,b) in C","highest_brand >= sum(b*x[s,b] for b with (s,b) in A) for each s in S"],"objective":"minimize highest_brand"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_slots = int(params["num_slots"])
    num_brands = int(params["num_brands"])
    adjacency_links = params["adjacency_links"]
    allowed_brands_per_slot = params["allowed_brands_per_slot"]

    slots = list(range(num_slots))
    brands = list(range(num_brands))
    slot_set = set(slots)
    brand_set = set(brands)

    allowed = {}
    for slot in slots:
        if isinstance(allowed_brands_per_slot, Mapping):
            key = slot if slot in allowed_brands_per_slot else str(slot)
            permitted = allowed_brands_per_slot[key]
        else:
            permitted = allowed_brands_per_slot[slot]

        allowed[slot] = sorted(set(permitted))
        if not set(allowed[slot]).issubset(brand_set):
            raise ValueError("Permitted brand identifier outside the brand range.")

    links = [tuple(link) for link in adjacency_links]
    for link in links:
        if len(link) != 2 or any(slot not in slot_set for slot in link):
            raise ValueError("Invalid adjacency link.")

    allowed_pairs = [
        (slot, brand)
        for slot in slots
        for brand in allowed[slot]
    ]
    conflict_triples = [
        (first_slot, second_slot, brand)
        for first_slot, second_slot in links
        for brand in allowed[first_slot]
        if brand in allowed[second_slot]
    ]

    model = pyo.ConcreteModel()
    model.S = pyo.Set(initialize=slots, ordered=True)
    model.B = pyo.Set(initialize=brands, ordered=True)
    model.E = pyo.Set(dimen=2, initialize=links)
    model.A = pyo.Set(dimen=2, initialize=allowed_pairs)
    model.C = pyo.Set(dimen=3, initialize=conflict_triples)

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.highest_brand = pyo.Var(domain=pyo.NonNegativeIntegers)

    def assignment_rule(instance, slot):
        # The explicit tuple preserves an infeasible native constraint
        # when a slot has no permitted brands.
        return (
            1,
            pyo.quicksum(instance.x[slot, brand] for brand in allowed[slot]),
            1,
        )

    model.assignment_constraints = pyo.Constraint(
        model.S, rule=assignment_rule
    )

    def adjacency_rule(instance, first_slot, second_slot, brand):
        return (
            instance.x[first_slot, brand]
            + instance.x[second_slot, brand]
            <= 1
        )

    model.adjacency_constraints = pyo.Constraint(
        model.C, rule=adjacency_rule
    )

    def highest_brand_rule(instance, slot):
        return instance.highest_brand >= pyo.quicksum(
            brand * instance.x[slot, brand]
            for brand in allowed[slot]
        )

    model.highest_brand_constraints = pyo.Constraint(
        model.S, rule=highest_brand_rule
    )
    model.objective_component = pyo.Objective(
        expr=model.highest_brand,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.objective_component))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}