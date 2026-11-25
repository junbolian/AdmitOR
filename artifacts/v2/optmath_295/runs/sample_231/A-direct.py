import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    vehicles = [1, 2, 3, 4, 5]
    regions = list(range(1, 32))

    costs = {
        1: params["cost_vehicle_1"],
        2: params["cost_vehicle_2"],
        3: params["cost_vehicle_3"],
        4: params["cost_vehicle_4"],
        5: params["cost_vehicle_5"],
    }

    model.V = pyo.Set(initialize=vehicles)
    model.E = pyo.Set(initialize=regions)

    model.x = pyo.Var(model.V, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(costs[v] * model.x[v] for v in model.V),
        sense=pyo.minimize,
    )

    coverage = {
        1: [4, 5],
        2: [4, 5],
        3: [3],
        4: [1, 2],
        5: [1, 2, 4],
        6: [1, 3, 4],
        7: [3, 4, 5],
        8: [3, 4],
        9: [1, 2, 3],
        10: [3, 4, 5],
        11: [3, 5],
        12: [1],
        13: [1, 4, 5],
        14: [3, 4],
        15: [1, 2, 5],
        16: [1, 2],
        17: [2],
        18: [5],
        19: [1, 4],
        20: [2],
        21: [3, 4, 5],
        22: [5],
        23: [1, 4],
        24: [2, 5],
        25: [1, 3, 5],
        26: [1, 2, 3],
        27: [5],
        28: [2, 4],
        29: [1, 3],
        30: [5],
        31: [1, 3],
    }

    def cover_rule(model, e):
        return sum(model.x[v] for v in coverage[e]) >= 1

    model.cover = pyo.Constraint(model.E, rule=cover_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}