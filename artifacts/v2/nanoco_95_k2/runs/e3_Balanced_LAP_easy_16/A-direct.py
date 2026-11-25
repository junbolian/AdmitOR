import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    n = 5

    model = pyo.ConcreteModel()
    model.drivers = pyo.RangeSet(0, n - 1)
    model.routes = pyo.RangeSet(0, n - 1)

    model.x = pyo.Var(model.drivers, model.routes, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.drivers for j in m.routes)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def driver_rule(m, i):
        return sum(m.x[i, j] for j in m.routes) == 1
    model.driver_con = pyo.Constraint(model.drivers, rule=driver_rule)

    def route_rule(m, j):
        return sum(m.x[i, j] for i in m.drivers) == 1
    model.route_con = pyo.Constraint(model.routes, rule=route_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}