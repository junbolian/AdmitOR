import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    strategy_costs = params["strategy_costs"]

    strategies = list(range(1, 9))

    coverage = {
        1: [1, 2, 3, 4, 7],
        2: [1, 3, 5, 6, 7, 8],
        3: [2, 3, 4, 5, 7],
        4: [5, 6],
        5: [2, 3, 5, 7, 8],
        6: [3, 6, 7, 8],
        7: [7],
        8: [4, 8],
        9: [2, 3, 6, 8],
        10: [2, 4, 7],
        11: [5, 6],
        12: [1, 2, 4, 7],
        13: [2, 3, 4, 6, 8],
        14: [1, 2, 3, 7],
        15: [5, 6],
        16: [1, 2, 3, 5, 6, 7, 8],
        17: [7],
        18: [1, 4, 6],
        19: [2, 5, 7],
        20: [3, 6],
        21: [1, 4, 5, 6],
        22: [2, 5, 6, 8],
        23: [1, 8],
        24: [4, 5, 6, 8],
        25: [1],
        26: [1, 2, 4, 8],
        27: [7],
        28: [2, 4],
        29: [1, 2, 4, 6],
        30: [7, 8],
        31: [3, 4],
        32: [5, 8],
        33: [4, 6],
        34: [3, 5, 7],
        35: [3, 5, 6],
        36: [1, 3, 4, 5],
        37: [2],
        38: [1, 2, 6],
        39: [1, 2, 3, 4, 7, 8],
    }

    segments = list(range(1, 40))

    model = pyo.ConcreteModel()

    model.STRAT = pyo.Set(initialize=strategies)
    model.SEG = pyo.Set(initialize=segments)

    model.x = pyo.Var(model.STRAT, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(strategy_costs[s - 1] * model.x[s] for s in strategies),
        sense=pyo.minimize,
    )

    def coverage_rule(m, seg):
        return sum(m.x[s] for s in coverage[seg]) >= 1

    model.cover = pyo.Constraint(model.SEG, rule=coverage_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}