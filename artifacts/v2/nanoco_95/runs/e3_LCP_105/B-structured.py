# IR: {"sets":{"slots":[0,1,2,3,4,5,6,7,8],"edges":[[0,1],[3,4],[2,7],[1,8],[2,3],[1,7],[0,5],[4,8],[2,5],[1,3]],"allowed":{"0":[0,1,2,3,4,5,6,7,8],"1":[1,2,3,5,6,7,8],"2":[0,1,2,3,4,5,6,7,8],"3":[0,3,5,6],"4":[0,1,2,3,5,6,7,8],"5":[0,3,5,7,8],"6":[0,1,2,3,4,6,7,8],"7":[3,4,5,7,8],"8":[0,1,2,4,5,6,7,8]},"permitted_pairs":"(s,b) for s in slots and b in allowed[s]","adjacency_triples":"(u,v,b) for (u,v) in edges and b in allowed[u] intersect allowed[v]"},"params":{},"decision_variables":{"x[s,b]":"Binary for permitted_pairs","highest_brand":"NonNegativeIntegers"},"constraints":["For each slot s: sum(x[s,b] for b in allowed[s]) = 1","For each adjacency triple (u,v,b): x[u,b] + x[v,b] <= 1","For each slot s: sum(b*x[s,b] for b in allowed[s]) <= highest_brand"],"objective":"minimize highest_brand"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # PARAMS is empty; the fixed lists and graph are structural data.
    slots = tuple(range(9))
    edges = (
        (0, 1),
        (3, 4),
        (2, 7),
        (1, 8),
        (2, 3),
        (1, 7),
        (0, 5),
        (4, 8),
        (2, 5),
        (1, 3),
    )
    allowed = {
        0: (0, 1, 2, 3, 4, 5, 6, 7, 8),
        1: (1, 2, 3, 5, 6, 7, 8),
        2: (0, 1, 2, 3, 4, 5, 6, 7, 8),
        3: (0, 3, 5, 6),
        4: (0, 1, 2, 3, 5, 6, 7, 8),
        5: (0, 3, 5, 7, 8),
        6: (0, 1, 2, 3, 4, 6, 7, 8),
        7: (3, 4, 5, 7, 8),
        8: (0, 1, 2, 4, 5, 6, 7, 8),
    }

    permitted_pairs = [
        (slot, brand)
        for slot in slots
        for brand in allowed[slot]
    ]
    adjacency_triples = [
        (left, right, brand)
        for left, right in edges
        for brand in allowed[left]
        if brand in allowed[right]
    ]

    model = pyo.ConcreteModel()
    model.slots = pyo.Set(initialize=slots, ordered=True)
    model.permitted_pairs = pyo.Set(
        dimen=2, initialize=permitted_pairs, ordered=True
    )
    model.adjacency_triples = pyo.Set(
        dimen=3, initialize=adjacency_triples, ordered=True
    )

    model.x = pyo.Var(model.permitted_pairs, domain=pyo.Binary)
    model.highest_brand = pyo.Var(domain=pyo.NonNegativeIntegers)

    def assignment_rule(model, slot):
        return sum(
            model.x[slot, brand] for brand in allowed[slot]
        ) == 1

    model.assignment_constraints = pyo.Constraint(
        model.slots, rule=assignment_rule
    )

    def adjacency_rule(model, left, right, brand):
        return model.x[left, brand] + model.x[right, brand] <= 1

    model.adjacency_constraints = pyo.Constraint(
        model.adjacency_triples, rule=adjacency_rule
    )

    def maximum_rule(model, slot):
        return sum(
            brand * model.x[slot, brand]
            for brand in allowed[slot]
        ) <= model.highest_brand

    model.maximum_constraints = pyo.Constraint(
        model.slots, rule=maximum_rule
    )

    model.objective = pyo.Objective(
        expr=model.highest_brand,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}