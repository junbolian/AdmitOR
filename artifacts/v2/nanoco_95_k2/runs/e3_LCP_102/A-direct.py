import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_zones = 10
    num_types = 10

    incompat = [
        (0, 1), (0, 4), (3, 4), (5, 7), (0, 6),
        (3, 9), (0, 5), (0, 8), (1, 3), (7, 8),
    ]

    allowed = {
        0: {0, 1, 2, 4, 5, 6, 7, 8, 9},
        1: {0, 1, 2, 3, 4, 5},
        2: {0, 1, 4, 5, 6, 7, 8},
        3: {0, 2, 3, 4, 7},
        4: {0, 1, 2, 4, 6, 7, 8, 9},
        5: {2, 3, 4, 6, 7},
        6: {0, 2, 3, 4, 5, 6, 8},
        7: {0, 1, 2, 3, 4, 5, 6, 7, 8, 9},
        8: {0, 1, 2, 3, 4, 5, 6, 7, 8, 9},
        9: {0, 2, 3, 5, 8, 9},
    }

    big_m = float(num_types)

    model = pyo.ConcreteModel()

    model.ZONES = pyo.RangeSet(0, num_zones - 1)
    model.TYPES = pyo.RangeSet(0, num_types - 1)

    # Only create assignment variables for allowed (zone, type) pairs
    allowed_pairs = [
        (zone, typ) for zone in range(num_zones) for typ in sorted(allowed[zone])
    ]

    model.assign = pyo.Var(allowed_pairs, domain=pyo.Binary)

    model.max_type = pyo.Var(domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(expr=model.max_type, sense=pyo.minimize)

    # Each zone assigned exactly one allowed type
    def zone_rule(mdl, z):
        return sum(mdl.assign[z, t] for t in mdl.TYPES if (z, t) in allowed_pairs) == 1

    model.zone_con = pyo.Constraint(model.ZONES, rule=zone_rule)

    # Incompatibility: paired zones cannot have same type
    # type(i) != type(j) encoded with a binary selector and big-M
    model.incompat_idx = pyo.RangeSet(1, len(incompat))

    model.diff_bin = pyo.Var(model.incompat_idx, domain=pyo.Binary)

    def chosen_expr(mdl, z):
        return sum(t * mdl.assign[z, t] for t in mdl.TYPES if (z, t) in allowed_pairs)

    def incompat_pos(mdl, idx):
        i, j = incompat[idx - 1]
        return chosen_expr(mdl, i) - chosen_expr(mdl, j) <= big_m * mdl.diff_bin[idx]

    def incompat_neg(mdl, idx):
        i, j = incompat[idx - 1]
        return chosen_expr(mdl, j) - chosen_expr(mdl, i) <= big_m * (1 - mdl.diff_bin[idx])

    model.incompat_pos = pyo.Constraint(model.incompat_idx, rule=incompat_pos)
    model.incompat_neg = pyo.Constraint(model.incompat_idx, rule=incompat_neg)

    # max_type >= chosen type for each zone
    def max_rule(mdl, z):
        return mdl.max_type >= chosen_expr(mdl, z)

    model.max_con = pyo.Constraint(model.ZONES, rule=max_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}