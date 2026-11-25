import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    areas = [1, 2, 3, 4, 5]
    model.A = pyo.Set(initialize=areas)

    cost = {
        1: params["cost_area_1"],
        2: params["cost_area_2"],
        3: params["cost_area_3"],
        4: params["cost_area_4"],
        5: params["cost_area_5"],
    }

    model.x = pyo.Var(model.A, domain=pyo.Binary)

    coverage = {
        1: [1, 2],
        2: [3, 4],
        3: [2, 3],
        4: [2, 3],
        5: [2, 3, 4],
        6: [1],
        7: [2, 3, 4],
        8: [3, 4],
        9: [2, 3],
        10: [1, 5],
        11: [2, 4],
        12: [3, 5],
        13: [3, 4],
        14: [4],
        15: [1, 4, 5],
    }

    model.E = pyo.Set(initialize=list(coverage.keys()))

    def cover_rule(m, e):
        return sum(m.x[a] for a in coverage[e]) >= 1

    model.cover = pyo.Constraint(model.E, rule=cover_rule)

    model.obj = pyo.Objective(expr=sum(cost[a] * model.x[a] for a in areas), sense=pyo.minimize)

    result = Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}