import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Structural data
    workers = list(range(1, 11))
    tasks = list(range(1, 23))

    capability = {
        1: [1, 2, 3, 4, 6, 9, 10],
        2: [5, 6, 8, 9, 10],
        3: [3, 4, 5, 10],
        4: [3, 5, 6],
        5: [3, 5, 7, 9, 10],
        6: [2, 4, 6, 10],
        7: [1, 3, 4, 5, 7, 8, 9],
        8: [2, 3, 4, 5, 7, 8],
        9: [1, 3, 5, 6, 7],
        10: [1, 4, 5, 6, 9, 10],
        11: [2, 4, 5, 7, 10],
        12: [4, 5, 8, 10],
        13: [2, 3, 7, 9],
        14: [2, 4, 5, 6, 8, 9],
        15: [3, 4, 5, 6, 7, 9],
        16: [3, 4, 6, 7, 9, 10],
        17: [1, 3, 4, 5, 7],
        18: [2, 4, 5, 6, 10],
        19: [1, 6, 7, 9],
        20: [3, 6, 7, 9, 10],
        21: [4, 5, 6],
        22: [1, 3, 4, 5, 8, 9],
    }

    costs = {w: params["worker_costs"][w - 1] for w in workers}

    model = pyo.ConcreteModel()

    model.W = pyo.Set(initialize=workers)
    model.T = pyo.Set(initialize=tasks)

    model.x = pyo.Var(model.W, domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(costs[w] * mdl.x[w] for w in workers)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def cover_rule(mdl, t):
        return sum(mdl.x[w] for w in capability[t]) >= 1

    model.cover = pyo.Constraint(model.T, rule=cover_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}