# IR: {"sets":{"A":"0..8","R":"0..6"},"params":{"availability":"params['availability'][a]","demand":"params['demand'][r]","cost":"params['cost'][a][r]","capacity":"params['capacity'][a][r]"},"variables":{"x[a,r]":"nonnegative integer"},"constraints":["sum(x[a,r] for r in R) <= availability[a] for each a in A","sum(capacity[a,r]*x[a,r] for a in A) >= demand[r] for each r in R"],"objective":"minimize sum(cost[a,r]*x[a,r] for a in A for r in R)"}

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

    model.availability = pyo.Param(
        model.aircraft_types,
        initialize=lambda mdl, a: availability[a],
    )
    model.demand = pyo.Param(
        model.routes,
        initialize=lambda mdl, r: demand[r],
    )
    model.cost = pyo.Param(
        model.aircraft_types,
        model.routes,
        initialize=lambda mdl, a, r: cost[a][r],
    )
    model.capacity = pyo.Param(
        model.aircraft_types,
        model.routes,
        initialize=lambda mdl, a, r: capacity[a][r],
    )

    model.x = pyo.Var(
        model.aircraft_types,
        model.routes,
        domain=pyo.NonNegativeIntegers,
    )

    model.availability_limits = pyo.Constraint(
        model.aircraft_types,
        rule=lambda mdl, a: (
            sum(mdl.x[a, r] for r in mdl.routes)
            <= mdl.availability[a]
        ),
    )
    model.demand_requirements = pyo.Constraint(
        model.routes,
        rule=lambda mdl, r: (
            sum(
                mdl.capacity[a, r] * mdl.x[a, r]
                for a in mdl.aircraft_types
            )
            >= mdl.demand[r]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[a, r] * model.x[a, r]
            for a in model.aircraft_types
            for r in model.routes
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # HiGHS raises this when no feasible solution can be loaded.
        # Leave unexpected solver errors visible to the calling harness.
        if "feasible solution" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective unavailable"}

    return {"objective": obj_val, "status": "optimal"}