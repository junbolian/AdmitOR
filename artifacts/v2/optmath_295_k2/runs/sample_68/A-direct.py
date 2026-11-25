import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = {
        1: params["cost_vehicle_1"],
        2: params["cost_vehicle_2"],
        3: params["cost_vehicle_3"],
        4: params["cost_vehicle_4"],
        5: params["cost_vehicle_5"],
        6: params["cost_vehicle_6"],
    }

    coverage = {
        1: [6],
        2: [2, 4, 6],
        3: [1, 3, 4],
        4: [3],
        5: [1, 5, 6],
        6: [1, 4],
        7: [3, 5],
        8: [4],
        9: [3, 5, 6],
        10: [4, 5, 6],
        11: [3, 4],
        12: [1, 3, 5, 6],
        13: [3, 4, 6],
    }

    vehicles = [1, 2, 3, 4, 5, 6]
    routes = sorted(coverage.keys())

    model = pyo.ConcreteModel()
    model.V = pyo.Set(initialize=vehicles)
    model.R = pyo.Set(initialize=routes)

    model.x = pyo.Var(model.V, within=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(costs[v] * model.x[v] for v in model.V),
        sense=pyo.minimize,
    )

    model.cover = pyo.Constraint(
        model.R,
        rule=lambda model, r: sum(model.x[v] for v in coverage[r]) >= 1,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}