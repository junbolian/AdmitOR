import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = params["costs"]
    n = len(costs)
    m_routes = len(costs[0])

    model = pyo.ConcreteModel()
    model.drivers = pyo.RangeSet(n)
    model.routes = pyo.RangeSet(m_routes)

    model.x = pyo.Var(model.drivers, model.routes, domain=pyo.Binary)

    def obj_rule(m):
        return sum(
            costs[i - 1][j - 1] * m.x[i, j]
            for i in m.drivers
            for j in m.routes
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    model.driver_constraint = pyo.Constraint(
        model.drivers,
        rule=lambda m, i: sum(m.x[i, j] for j in m.routes) == 1,
    )
    model.route_constraint = pyo.Constraint(
        model.routes,
        rule=lambda m, j: sum(m.x[i, j] for i in m.drivers) == 1,
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception as exc:
        return {"objective": None, "status": str(exc)[:100]}

    return {"objective": obj_val, "status": "optimal"}