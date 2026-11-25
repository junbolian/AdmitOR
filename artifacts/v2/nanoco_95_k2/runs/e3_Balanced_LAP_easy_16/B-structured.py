# IR: {"sets":{"drivers":[0,1,2,3,4],"routes":[0,1,2,3,4]},"params":{"cost":"params['cost'][i][j], real-valued 5x5 matrix"},"variables":{"x[i,j]":"binary"},"constraints":["For each driver i: sum(x[i,j] for j in routes) == 1","For each route j: sum(x[i,j] for i in drivers) == 1"],"objective":"Minimize sum(cost[i,j]*x[i,j] for i in drivers for j in routes)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.drivers = pyo.RangeSet(0, 4)
    model.routes = pyo.RangeSet(0, 4)

    model.cost = pyo.Param(
        model.drivers,
        model.routes,
        initialize=lambda instance, i, j: params["cost"][i][j],
        within=pyo.Reals,
    )

    model.x = pyo.Var(
        model.drivers,
        model.routes,
        domain=pyo.Binary,
    )

    def driver_assignment_rule(instance, i):
        return sum(instance.x[i, j] for j in instance.routes) == 1

    model.driver_assignment = pyo.Constraint(
        model.drivers,
        rule=driver_assignment_rule,
    )

    def route_assignment_rule(instance, j):
        return sum(instance.x[i, j] for i in instance.drivers) == 1

    model.route_assignment = pyo.Constraint(
        model.routes,
        rule=route_assignment_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.x[i, j]
            for i in model.drivers
            for j in model.routes
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}