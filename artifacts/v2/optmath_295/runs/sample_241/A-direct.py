import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    program_costs = params["program_costs"]

    programs = list(range(17))
    topics = list(range(37))

    coverage = {
        0: [1, 2, 4, 6, 9, 10, 13, 14, 15, 17],
        1: [4, 5, 7, 8, 13, 17],
        2: [4, 5, 7, 8, 10, 11, 12, 15, 16, 17],
        3: [5, 6, 7, 11, 13, 16, 17],
        4: [2, 3, 4, 6, 8, 9, 10, 16],
        5: [2, 3, 4, 7, 11, 17],
        6: [4, 5, 9, 13, 17],
        7: [1, 4, 6, 7, 8, 10, 12, 13, 15, 17],
        8: [1, 7, 8, 12, 15, 16],
        9: [2, 3, 4, 5, 6, 9, 13, 16],
        10: [3, 7, 9, 11, 14, 15],
        11: [5, 7, 10, 12, 14],
        12: [1, 3, 5, 9, 10, 11, 13],
        13: [2, 7, 8, 13, 14, 15, 16],
        14: [2, 5, 8, 13, 16],
        15: [2, 3, 9],
        16: [2, 3, 4, 5, 7, 10, 13, 16],
        17: [3, 6, 7, 8, 9, 15, 16],
        18: [7, 9, 10, 13, 14, 15],
        19: [2, 3, 4, 5, 6, 11, 12, 14, 17],
        20: [1, 2, 7, 9, 12, 14, 16],
        21: [3, 4, 6, 9, 11, 16],
        22: [2, 6, 10, 11, 14],
        23: [1, 3, 6, 7, 11, 12, 13, 15, 16],
        24: [1, 3, 7, 8, 11, 12, 15],
        25: [3, 5, 10, 11, 12, 16],
        26: [6, 7, 9, 10, 11, 12, 16],
        27: [3, 4, 6, 7, 11, 12],
        28: [3, 6, 7, 10, 13, 16, 17],
        29: [2, 6, 9, 10, 13, 15, 16, 17],
        30: [2, 6, 7, 8, 9, 11, 12, 13, 17],
        31: [1, 7, 9, 13, 15],
        32: [1, 3, 6, 9, 13, 14],
        33: [2, 3, 6, 13, 14, 15, 17],
        34: [1, 2, 3, 6, 10, 11, 12, 17],
        35: [4, 5, 7, 12, 13],
        36: [2, 8, 11, 16],
    }

    cover_map = {t: set(p - 1 for p in coverage[t]) for t in topics}

    model = pyo.ConcreteModel()
    model.x = pyo.Var(programs, domain=pyo.Binary)

    def objective_rule(m):
        return sum(program_costs[i] * m.x[i] for i in programs)

    model.min_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def cover_rule(m, t):
        return sum(m.x[i] for i in cover_map[t]) >= 1

    model.cover_con = pyo.Constraint(topics, rule=cover_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.min_cost))
    return {"objective": obj_val, "status": "optimal"}