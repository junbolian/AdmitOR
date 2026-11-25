# {"sets":{"A":"0..8","R":"0..6"},"params":{"availability":"A -> number, from params['availability']","demand":"R -> number, from params['demand']","cost":"A x R -> number, from params['cost']","capacity":"A x R -> number, from params['capacity']"},"variables":{"x[a,r]":"nonnegative integer, for a in A and r in R"},"constraints":["sum(x[a,r] for r in R) <= availability[a], for each a in A","sum(capacity[a,r]*x[a,r] for a in A) >= demand[r], for each r in R"],"objective":"minimize sum(cost[a,r]*x[a,r] for a in A and r in R)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    availability = params["availability"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.aircraft_types = pyo.RangeSet(0, 8)
    model.routes = pyo.RangeSet(0, 6)

    model.aircraft_available = pyo.Param(
        model.aircraft_types,
        initialize=lambda mdl, a: availability[a],
        within=pyo.Reals,
    )
    model.passenger_demand = pyo.Param(
        model.routes,
        initialize=lambda mdl, r: demand[r],
        within=pyo.Reals,
    )
    model.assignment_cost = pyo.Param(
        model.aircraft_types,
        model.routes,
        initialize=lambda mdl, a, r: cost[a][r],
        within=pyo.Reals,
    )
    model.passenger_capacity = pyo.Param(
        model.aircraft_types,
        model.routes,
        initialize=lambda mdl, a, r: capacity[a][r],
        within=pyo.Reals,
    )

    model.x = pyo.Var(
        model.aircraft_types,
        model.routes,
        domain=pyo.NonNegativeIntegers,
    )

    def availability_rule(mdl, a):
        return (
            sum(mdl.x[a, r] for r in mdl.routes)
            <= mdl.aircraft_available[a]
        )

    model.availability_limits = pyo.Constraint(
        model.aircraft_types,
        rule=availability_rule,
    )

    def demand_rule(mdl, r):
        return (
            sum(
                mdl.passenger_capacity[a, r] * mdl.x[a, r]
                for a in mdl.aircraft_types
            )
            >= mdl.passenger_demand[r]
        )

    model.demand_requirements = pyo.Constraint(
        model.routes,
        rule=demand_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[a, r] * model.x[a, r]
            for a in model.aircraft_types
            for r in model.routes
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
    except (RuntimeError, ValueError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}