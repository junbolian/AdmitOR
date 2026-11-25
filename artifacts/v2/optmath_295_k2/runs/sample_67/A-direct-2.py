import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    activation_costs = params["hub_activation_costs"]

    hubs = list(range(1, 16))
    routes = list(range(1, 17))

    coverage = {
        1: [2, 3, 4, 7, 11, 13],
        2: [10, 12, 15],
        3: [1, 5, 6, 8, 11, 12, 13, 14],
        4: [2, 3, 4, 6, 7, 10, 12, 14],
        5: [1, 2, 3, 10, 13],
        6: [1, 2, 3, 6, 8, 10, 11, 12, 14],
        7: [3, 4, 5, 7, 8, 10, 11, 13, 14],
        8: [1, 2, 3, 7, 9, 12, 13],
        9: [1, 4, 7, 10, 12, 13, 14],
        10: [1, 3, 4, 5, 7, 10, 11, 13, 14, 15],
        11: [1, 4, 7, 9, 13, 14],
        12: [3, 4, 6, 8, 10, 11, 12, 13, 14, 15],
        13: [1, 2, 4, 5, 7, 11, 13, 14],
        14: [1, 4, 5, 6, 9, 12, 14, 15],
        15: [2, 6, 7, 12, 13, 14],
        16: [1, 4, 8, 11, 12, 14, 15],
    }

    model = pyo.ConcreteModel()
    model.HUBS = pyo.Set(initialize=hubs)
    model.ROUTES = pyo.Set(initialize=routes)
    model.x = pyo.Var(model.HUBS, within=pyo.Binary)

    def _route_rule(mdl, r):
        return sum(mdl.x[h] for h in coverage[r]) >= 1

    model.route_cover = pyo.Constraint(model.ROUTES, rule=_route_rule)

    model.total_cost = pyo.Objective(
        expr=sum(activation_costs[h - 1] * model.x[h] for h in model.HUBS),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}