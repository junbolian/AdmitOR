import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    program_costs = params["program_costs"]

    n_programs = 17
    n_topics = 37

    # Topic i (1-indexed) covered by which programs (1-indexed)
    coverage = {
        1: [1, 2, 4, 6, 9, 10, 13, 14, 15, 17],
        2: [4, 5, 7, 8, 13, 17],
        3: [4, 5, 7, 8, 10, 11, 12, 15, 16, 17],
        4: [5, 6, 7, 11, 13, 16, 17],
        5: [2, 3, 4, 6, 8, 9, 10, 16],
        6: [2, 3, 4, 7, 11, 17],
        7: [4, 5, 9, 13, 17],
        8: [1, 4, 6, 7, 8, 10, 12, 13, 15, 17],
        9: [1, 7, 8, 12, 15, 16],
        10: [2, 3, 4, 5, 6, 9, 13, 16],
        11: [3, 7, 9, 11, 14, 15],
        12: [5, 7, 10, 12, 14],
        13: [1, 3, 5, 9, 10, 11, 13],
        14: [2, 7, 8, 13, 14, 15, 16],
        15: [2, 5, 8, 13, 16],
        16: [2, 3, 9],
        17: [2, 3, 4, 5, 7, 10, 13, 16],
        18: [3, 6, 7, 8, 9, 15, 16],
        19: [7, 9, 10, 13, 14, 15],
        20: [2, 3, 4, 5, 6, 11, 12, 14, 17],
        21: [1, 2, 7, 9, 12, 14, 16],
        22: [3, 4, 6, 9, 11, 16],
        23: [2, 6, 10, 11, 14],
        24: [1, 3, 6, 7, 11, 12, 13, 15, 16],
        25: [1, 3, 7, 8, 11, 12, 15],
        26: [3, 5, 10, 11, 12, 16],
        27: [6, 7, 9, 10, 11, 12, 16],
        28: [3, 4, 6, 7, 11, 12],
        29: [3, 6, 7, 10, 13, 16, 17],
        30: [2, 6, 9, 10, 13, 15, 16, 17],
        31: [2, 6, 7, 8, 9, 11, 12, 13, 17],
        32: [1, 7, 9, 13, 15],
        33: [1, 3, 6, 9, 13, 14],
        34: [2, 3, 6, 13, 14, 15, 17],
        35: [1, 2, 3, 6, 10, 11, 12, 17],
        36: [4, 5, 7, 12, 13],
        37: [2, 8, 11, 16],
    }

    programs = list(range(1, n_programs + 1))
    topics = list(range(1, n_topics + 1))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(programs, domain=pyo.Binary)

    model.cost = pyo.Objective(
        expr=sum(program_costs[i - 1] * model.x[i] for i in programs),
        sense=pyo.minimize,
    )

    def cover_rule(mdl, t):
        return sum(mdl.x[p] for p in coverage[t]) >= 1

    model.cover = pyo.Constraint(topics, rule=cover_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}