import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_slots = 9
    n_brands = 9
    edges = [
        (0, 1), (3, 4), (2, 7), (1, 8), (2, 3),
        (1, 7), (0, 5), (4, 8), (2, 5), (1, 3),
    ]
    allowed = {
        0: {0, 1, 2, 3, 4, 5, 6, 7, 8},
        1: {1, 2, 3, 5, 6, 7, 8},
        2: {0, 1, 2, 3, 4, 5, 6, 7, 8},
        3: {0, 3, 5, 6},
        4: {0, 1, 2, 3, 5, 6, 7, 8},
        5: {0, 3, 5, 7, 8},
        6: {0, 1, 2, 3, 4, 6, 7, 8},
        7: {3, 4, 5, 7, 8},
        8: {0, 1, 2, 4, 5, 6, 7, 8},
    }

    slots = list(range(n_slots))
    brands = list(range(n_brands))

    model = pyo.ConcreteModel()

    # x[s, b] = 1 if slot s assigned brand b
    model.x = pyo.Var(
        [(s, b) for s in slots for b in brands if b in allowed[s]],
        domain=pyo.Binary,
    )

    # z = maximum brand identifier used
    model.z = pyo.Var(domain=pyo.NonNegativeReals)

    # Each slot gets exactly one brand
    def one_brand_rule(m, s):
        return sum(m.x[s, b] for b in brands if b in allowed[s]) == 1

    model.one_brand = pyo.Constraint(slots, rule=one_brand_rule)

    # Adjacent slots must have different brands
    def diff_rule(m, i, j):
        return sum(
            m.x[i, b] for b in brands if b in allowed[i]
        ) + sum(
            m.x[j, b] for b in brands if b in allowed[j]
        ) <= 1000  # placeholder replaced below

    # Build difference constraints directly per shared brand
    diff_constraints = []
    for (i, j) in edges:
        shared = allowed[i] & allowed[j]
        for b in shared:
            diff_constraints.append((i, j, b))

    model.diff = pyo.ConstraintList()
    for (i, j, b) in diff_constraints:
        model.diff.add(model.x[i, b] + model.x[j, b] <= 1)

    # z >= b * x[s, b] for all assignments
    model.z_bound = pyo.ConstraintList()
    for s in slots:
        for b in brands:
            if b in allowed[s]:
                model.z_bound.add(b * model.x[s, b] <= model.z)

    model.objective = pyo.Objective(expr=model.z, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.objective))
    return {"objective": obj_val, "status": "optimal"}