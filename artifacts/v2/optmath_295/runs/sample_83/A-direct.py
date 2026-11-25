import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    populations = params["populations"]
    tower_costs = params["tower_costs"]
    budget = params["budget"]

    areas = list(range(24))
    towers = list(range(18))

    coverage = {
        0: [1, 2, 8, 14, 15, 17],
        1: [0, 3, 6, 7, 8, 9, 12],
        2: [0, 1, 4, 5, 7, 10, 11, 12, 16],
        3: [1, 2, 3, 5, 9, 12, 13, 15, 17],
        4: [1, 2, 3, 7, 8, 10, 11, 16],
        5: [1, 4, 5, 6, 8, 11, 12, 14, 16],
        6: [0, 2, 3, 4, 5, 7, 10, 11, 13, 14, 16],
        7: [1, 2, 4, 5, 7, 10, 11, 13, 14, 16, 17],
        8: [2, 3, 10, 13, 14, 16],
        9: [2, 3, 4, 5, 6, 7, 8, 10, 11, 14, 15, 17],
        10: [0, 1, 5, 12, 16, 17],
        11: [2, 3, 5, 6, 7, 10, 11, 13, 14, 15, 16, 17],
        12: [0, 1, 2, 7, 9, 10, 12, 14, 15, 17],
        13: [0, 1, 2, 3, 6, 10, 11, 14, 15, 16],
        14: [0, 2, 4, 7, 8, 10, 11, 14, 15, 16],
        15: [0, 1, 4, 5, 7, 10, 13, 15, 16, 17],
        16: [0, 3, 4, 8, 10, 12, 13, 14, 15],
        17: [3, 4, 5, 6, 8, 10, 12, 14],
        18: [7, 8, 9, 15],
        19: [0, 3, 6, 7, 8, 9, 13, 15, 17],
        20: [2, 4, 7, 8, 11, 12, 13, 14, 15, 16],
        21: [1, 5, 8, 10, 11, 12],
        22: [1, 2, 4, 6, 8, 12, 14, 16],
        23: [0, 1, 2, 5, 6, 10, 12, 13, 15, 16, 17],
    }

    model = pyo.ConcreteModel()

    model.TOWERS = pyo.Set(initialize=towers, ordered=True)
    model.AREAS = pyo.Set(initialize=areas, ordered=True)

    model.build = pyo.Var(model.TOWERS, domain=pyo.Binary)
    model.covered = pyo.Var(model.AREAS, domain=pyo.Binary)

    model.budget_con = pyo.Constraint(
        expr=sum(tower_costs[j] * model.build[j] for j in model.TOWERS) <= budget
    )

    def cover_rule(mdl, i):
        return mdl.covered[i] <= sum(mdl.build[j] for j in coverage[i])

    model.cover_con = pyo.Constraint(model.AREAS, rule=cover_rule)

    model.obj = pyo.Objective(
        expr=sum(populations[i] * model.covered[i] for i in model.AREAS),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}