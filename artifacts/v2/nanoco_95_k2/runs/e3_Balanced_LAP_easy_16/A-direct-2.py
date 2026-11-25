import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    n_drivers = len(cost)
    n_routes = len(cost[0])

    model = pyo.ConcreteModel()
    model.DRIVERS = pyo.RangeSet(0, n_drivers - 1)
    model.ROUTES = pyo.RangeSet(0, n_routes - 1)

    model.x = pyo.Var(model.DRIVERS, model.ROUTES, domain=pyo.Binary)

    model.total_cost = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j]
                 for i in model.DRIVERS for j in model.ROUTES),
        sense=pyo.minimize,
    )

    model.driver_assign = pyo.Constraint(
        model.DRIVERS,
        rule=lambda mm, i: sum(mm.x[i, j] for j in mm.ROUTES) == 1,
    )
    model.route_assign = pyo.Constraint(
        model.ROUTES,
        rule=lambda mm, j: sum(mm.x[i, j] for i in mm.DRIVERS) == 1,
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible or failed"}