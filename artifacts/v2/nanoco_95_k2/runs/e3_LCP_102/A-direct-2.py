import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_zones = 10
    incompat = [
        (0, 1), (0, 4), (3, 4), (5, 7), (0, 6),
        (3, 9), (0, 5), (0, 8), (1, 3), (7, 8),
    ]
    zones = list(range(n_zones))
    types = list(range(10))

    permitted = {
        0: [0, 1, 2, 4, 5, 6, 7, 8, 9],
        1: [0, 1, 2, 3, 4, 5],
        2: [0, 1, 4, 5, 6, 7, 8],
        3: [0, 2, 3, 4, 7],
        4: [0, 1, 2, 4, 6, 7, 8, 9],
        5: [2, 3, 4, 6, 7],
        6: [0, 2, 3, 4, 5, 6, 8],
        7: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        8: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        9: [0, 2, 3, 5, 8, 9],
    }

    model = pyo.ConcreteModel()

    allowed = [(z, t) for z in zones for t in permitted[z]]
    model.x = pyo.Var(allowed, domain=pyo.Binary)
    model.zmax = pyo.Var(domain=pyo.NonNegativeReals)

    def one_type_rule(m, z):
        return sum(m.x[z, t] for t in permitted[z]) == 1

    model.one_type = pyo.Constraint(zones, rule=one_type_rule)

    def incompat_rule(m, a, b):
        common = [t for t in permitted[a] if t in permitted[b]]
        return sum(m.x[a, t] for t in common) + sum(m.x[b, t] for t in common) <= 1

    model.incompat = pyo.Constraint(incompat, rule=incompat_rule)

    def zmax_rule(m, z):
        return m.zmax >= sum(t * m.x[z, t] for t in permitted[z])

    model.zmax_def = pyo.Constraint(zones, rule=zmax_rule)

    model.obj = pyo.Objective(expr=model.zmax, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}