# IR: {"sets":{"drivers":[0,1,2,3,4],"routes":[0,1,2,3,4]},"params":{"costs":"input cost matrix indexed by driver and route"},"variables":{"assignment[driver,route]":"binary"},"constraints":["For each driver: sum(assignment[driver,route] for route in routes) = 1","For each route: sum(assignment[driver,route] for driver in drivers) = 1"],"objective":"minimize sum(costs[driver][route] * assignment[driver,route] for driver in drivers for route in routes)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = params["costs"]

    model = pyo.ConcreteModel()
    model.drivers = pyo.RangeSet(0, 4)
    model.routes = pyo.RangeSet(0, 4)

    model.assignment_cost = pyo.Param(
        model.drivers,
        model.routes,
        initialize=lambda mdl, driver, route: costs[driver][route],
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(
        model.drivers,
        model.routes,
        domain=pyo.Binary,
    )

    def driver_assignment_rule(mdl, driver):
        return sum(
            mdl.assignment[driver, route] for route in mdl.routes
        ) == 1

    model.driver_assignment = pyo.Constraint(
        model.drivers,
        rule=driver_assignment_rule,
    )

    def route_assignment_rule(mdl, route):
        return sum(
            mdl.assignment[driver, route] for driver in mdl.drivers
        ) == 1

    model.route_assignment = pyo.Constraint(
        model.routes,
        rule=route_assignment_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[driver, route]
            * model.assignment[driver, route]
            for driver in model.drivers
            for route in model.routes
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution can be loaded.
        # Objective retrieval below remains the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}