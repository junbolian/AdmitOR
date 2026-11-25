import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["setup_cost"]

    num_zones = 21
    num_locs = len(cost)

    coverage = {
        1: [1, 2, 4, 6, 7, 8, 11],
        2: [3, 4, 5, 6, 7, 9, 11, 13],
        3: [1, 3, 4, 5, 7, 8, 9, 10, 11],
        4: [1, 4, 8, 10, 13],
        5: [1, 2, 4, 6, 9, 10],
        6: [3, 4, 5, 6, 7, 8, 10, 13],
        7: [2, 4, 5, 6, 7, 9, 10, 11, 12, 13],
        8: [5, 8, 11, 12],
        9: [1, 3, 4, 7, 8, 10, 12, 13],
        10: [2, 4, 6, 8, 11, 12],
        11: [3, 4, 8, 9, 11],
        12: [2, 4, 5, 7, 11, 12],
        13: [1, 2, 3, 5, 7, 9, 10, 13],
        14: [1, 2, 6, 8, 9, 10, 12, 13],
        15: [1, 3, 5, 10],
        16: [1, 5, 6, 8, 13],
        17: [1, 2, 3, 4, 5, 6, 8, 9, 12],
        18: [1, 4, 6, 9, 11, 13],
        19: [4, 6, 8],
        20: [1, 2, 3, 4, 5, 11, 13],
        21: [2, 3, 6, 9],
    }

    model = pyo.ConcreteModel()
    model.LOCS = pyo.RangeSet(1, num_locs)
    model.ZONES = pyo.RangeSet(1, num_zones)

    model.x = pyo.Var(model.LOCS, within=pyo.Binary)

    def obj_rule(m):
        return sum(cost[i - 1] * m.x[i] for i in m.LOCS)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def cover_rule(m, z):
        return sum(m.x[i] for i in coverage[z]) >= 1

    model.cover = pyo.Constraint(model.ZONES, rule=cover_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}