# IR: {"sets":{"drivers":[0,1,2,3,4],"routes":[0,1,2,3,4]},"params":{"cost":{"type":"real","indices":["drivers","routes"],"source":"params['cost']"}},"variables":{"assignment":{"type":"binary","indices":["drivers","routes"]}},"constraints":["For each driver i: sum(assignment[i,j] for j in routes) == 1","For each route j: sum(assignment[i,j] for i in drivers) == 1"],"objective":{"sense":"minimize","expression":"sum(cost[i,j] * assignment[i,j] for i in drivers for j in routes)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = params["cost"]

    model = pyo.ConcreteModel()
    model.drivers = pyo.RangeSet(0, 4)
    model.routes = pyo.RangeSet(0, 4)

    model.cost = pyo.Param(
        model.drivers,
        model.routes,
        initialize=lambda mdl, i, j: costs[i][j],
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(
        model.drivers,
        model.routes,
        domain=pyo.Binary,
    )

    def driver_assignment_rule(mdl, i):
        return sum(mdl.assignment[i, j] for j in mdl.routes) == 1

    model.driver_assignment = pyo.Constraint(
        model.drivers,
        rule=driver_assignment_rule,
    )

    def route_assignment_rule(mdl, j):
        return sum(mdl.assignment[i, j] for i in mdl.drivers) == 1

    model.route_assignment = pyo.Constraint(
        model.routes,
        rule=route_assignment_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.assignment[i, j]
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
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}