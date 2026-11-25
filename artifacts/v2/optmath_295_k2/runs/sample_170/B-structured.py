# IR: {"sets":{"A":"0..4 (aircraft types)","R":"0..5 (routes)"},"params":{"availability":"availability[a]","demand":"demand[r]","capability":"capability[a][r]","cost":"cost[a][r]"},"variables":{"x[a,r]":"nonnegative integer"},"constraints":["forall a in A: sum(r in R, x[a,r]) <= availability[a]","forall r in R: sum(a in A, capability[a,r]*x[a,r]) >= demand[r]"],"objective":"minimize sum(a in A, r in R, cost[a,r]*x[a,r])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using vectors and matrices indexed by aircraft and route."""
    availability = params["availability"]
    demand = params["demand"]
    capability = params["capability"]
    cost = params["cost"]

    model = pyo.ConcreteModel()

    model.aircraft_types = pyo.RangeSet(0, 4)
    model.routes = pyo.RangeSet(0, 5)

    model.aircraft_availability = pyo.Param(
        model.aircraft_types,
        initialize={a: availability[a] for a in model.aircraft_types},
    )
    model.route_demand = pyo.Param(
        model.routes,
        initialize={r: demand[r] for r in model.routes},
    )
    model.capacity_contribution = pyo.Param(
        model.aircraft_types,
        model.routes,
        initialize={
            (a, r): capability[a][r]
            for a in model.aircraft_types
            for r in model.routes
        },
    )
    model.assignment_cost = pyo.Param(
        model.aircraft_types,
        model.routes,
        initialize={
            (a, r): cost[a][r]
            for a in model.aircraft_types
            for r in model.routes
        },
    )

    model.x = pyo.Var(
        model.aircraft_types,
        model.routes,
        domain=pyo.NonNegativeIntegers,
    )

    def availability_rule(instance, a):
        return (
            sum(instance.x[a, r] for r in instance.routes)
            <= instance.aircraft_availability[a]
        )

    model.availability_limit = pyo.Constraint(
        model.aircraft_types,
        rule=availability_rule,
    )

    def demand_rule(instance, r):
        return (
            sum(
                instance.capacity_contribution[a, r] * instance.x[a, r]
                for a in instance.aircraft_types
            )
            >= instance.route_demand[r]
        )

    model.demand_coverage = pyo.Constraint(
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
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}