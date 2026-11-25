import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = params["hub_activation_costs"]
    hubs = list(range(1, 16))

    routes = {
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
    model.ROUTES = pyo.Set(initialize=list(routes.keys()))

    model.x = pyo.Var(model.HUBS, within=pyo.Binary)

    def cost_rule(m):
        return sum(costs[i - 1] * m.x[i] for i in m.HUBS)

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def cover_rule(m, r):
        return sum(m.x[h] for h in routes[r]) >= 1

    model.cover = pyo.Constraint(model.ROUTES, rule=cover_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}