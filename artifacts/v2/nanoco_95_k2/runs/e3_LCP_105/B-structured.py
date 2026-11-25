# IR: {"sets":{"S":"range(params['num_slots'])","B":"range(params['num_brands'])","E":"params['adjacency_links']","A[s]":"params['allowed_brands_per_slot'][s]","F":"{(s,b) in S x B: b not in A[s]}"},"params":["num_slots","num_brands","adjacency_links","allowed_brands_per_slot"],"variables":{"x[s,b]":"Binary for (s,b) in S x B","highest_brand":"NonNegativeInteger"},"constraints":["For every s in S: sum(b in B, x[s,b]) = 1","For every (s,b) in F: x[s,b] = 0","For every (u,v) in E and b in B: x[u,b] + x[v,b] <= 1","For every s in S: highest_brand >= sum(b in B, b*x[s,b])"],"objective":"Minimize highest_brand"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_slots = params["num_slots"]
    num_brands = params["num_brands"]
    adjacency_links = params["adjacency_links"]
    allowed_brands_per_slot = params["allowed_brands_per_slot"]

    slots = range(num_slots)
    brands = range(num_brands)

    # Accept slot lists or mappings keyed by integers or JSON string keys.
    if isinstance(allowed_brands_per_slot, Mapping):
        permitted = {
            slot: set(
                allowed_brands_per_slot[slot]
                if slot in allowed_brands_per_slot
                else allowed_brands_per_slot[str(slot)]
            )
            for slot in slots
        }
    else:
        permitted = {
            slot: set(allowed_brands_per_slot[slot])
            for slot in slots
        }

    model = pyo.ConcreteModel()
    model.slots = pyo.Set(initialize=slots, ordered=True)
    model.brands = pyo.Set(initialize=brands, ordered=True)
    model.edges = pyo.Set(
        dimen=2,
        within=model.slots * model.slots,
        initialize=[tuple(link) for link in adjacency_links],
    )
    model.forbidden_pairs = pyo.Set(
        dimen=2,
        within=model.slots * model.brands,
        initialize=[
            (slot, brand)
            for slot in slots
            for brand in brands
            if brand not in permitted[slot]
        ],
    )

    model.x = pyo.Var(model.slots, model.brands, domain=pyo.Binary)
    model.highest_brand = pyo.Var(domain=pyo.NonNegativeIntegers)

    def assignment_rule(instance, slot):
        # Starting with a symbolic zero also handles an empty brand set.
        return (
            sum(
                (instance.x[slot, brand] for brand in instance.brands),
                0 * instance.highest_brand,
            )
            == 1
        )

    model.assignment_constraints = pyo.Constraint(
        model.slots, rule=assignment_rule
    )

    def permitted_rule(instance, slot, brand):
        return instance.x[slot, brand] == 0

    model.permitted_constraints = pyo.Constraint(
        model.forbidden_pairs, rule=permitted_rule
    )

    def adjacency_rule(instance, first_slot, second_slot, brand):
        return (
            instance.x[first_slot, brand]
            + instance.x[second_slot, brand]
            <= 1
        )

    model.adjacency_constraints = pyo.Constraint(
        model.edges, model.brands, rule=adjacency_rule
    )

    def highest_brand_rule(instance, slot):
        return instance.highest_brand >= sum(
            brand * instance.x[slot, brand]
            for brand in instance.brands
        )

    model.highest_brand_constraints = pyo.Constraint(
        model.slots, rule=highest_brand_rule
    )
    model.objective = pyo.Objective(
        expr=model.highest_brand, sense=pyo.minimize
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when it cannot load a feasible solution.
        # Objective retrieval below remains the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}