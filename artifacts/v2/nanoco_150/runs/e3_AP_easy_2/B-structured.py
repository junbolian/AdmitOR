# IR: {"sets":{"drivers":[0,1,2,3,4],"rides":[0,1,2,3,4]},"params":{"cost_matrix":"params['cost_matrix'][driver][ride]"},"variables":{"assignment[driver,ride]":"binary"},"constraints":["For each driver: sum(assignment[driver,ride] for ride in rides) == 1","For each ride: sum(assignment[driver,ride] for driver in drivers) == 1"],"objective":"minimize sum(cost_matrix[driver][ride] * assignment[driver,ride] for driver in drivers for ride in rides)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]

    model = pyo.ConcreteModel()
    model.drivers = pyo.RangeSet(0, 4)
    model.rides = pyo.RangeSet(0, 4)

    model.dispatch_cost = pyo.Param(
        model.drivers,
        model.rides,
        initialize=lambda mdl, driver, ride: cost_matrix[driver][ride],
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(
        model.drivers,
        model.rides,
        domain=pyo.Binary,
    )

    def driver_assignment_rule(mdl, driver):
        return sum(
            mdl.assignment[driver, ride] for ride in mdl.rides
        ) == 1

    model.driver_assignment = pyo.Constraint(
        model.drivers,
        rule=driver_assignment_rule,
    )

    def ride_assignment_rule(mdl, ride):
        return sum(
            mdl.assignment[driver, ride] for driver in mdl.drivers
        ) == 1

    model.ride_assignment = pyo.Constraint(
        model.rides,
        rule=ride_assignment_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.dispatch_cost[driver, ride] * model.assignment[driver, ride]
            for driver in model.drivers
            for ride in model.rides
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}