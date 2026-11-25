import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    program_costs = params["program_costs"]

    num_programs = len(program_costs)
    num_topics = 37

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

    model = pyo.ConcreteModel()

    model.PROGRAMS = pyo.Set(initialize=list(range(1, num_programs + 1)))
    model.TOPICS = pyo.Set(initialize=list(range(1, num_topics + 1)))

    model.select = pyo.Var(model.PROGRAMS, domain=pyo.Binary)

    def objective_rule(m):
        return sum(program_costs[p - 1] * m.select[p] for p in m.PROGRAMS)

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def coverage_rule(m, t):
        return sum(m.select[p] for p in coverage[t]) >= 1

    model.cover = pyo.Constraint(model.TOPICS, rule=coverage_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}