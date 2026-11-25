import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    route_cost = params["route_cost"]
    route_min = params["route_min"]
    route_max = params["route_max"]

    routes = [
        (0, 1), (0, 2), (0, 5),
        (1, 0), (1, 2), (1, 5),
        (2, 1), (2, 3), (2, 5),
        (3, 0), (3, 1), (3, 2), (3, 4),
        (4, 3), (4, 5),
        (5, 0), (5, 2), (5, 4),
    ]
    R = range(len(routes))
    W = range(6)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(R, domain=pyo.NonNegativeReals)

    def cost_rule(m):
        return sum(route_cost[i] * m.x[i] for i in R)

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    model.min_obligation = pyo.Constraint(
        R, rule=lambda m, i: m.x[i] >= route_min[i]
    )
    model.max_capacity = pyo.Constraint(
        R, rule=lambda m, i: m.x[i] <= route_max[i]
    )

    def balance_rule(m, w):
        inflow = sum(m.x[i] for i in R if routes[i][1] == w)
        outflow = sum(m.x[i] for i in R if routes[i][0] == w)
        return inflow == outflow

    model.balance = pyo.Constraint(W, rule=balance_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))

    return {"objective": obj_val, "status": "optimal"}