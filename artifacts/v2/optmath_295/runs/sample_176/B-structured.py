# IR: {"sets":{"I":"0..8","J":"0..6"},"params":{"availability":"I -> nonnegative integer","demand":"J -> nonnegative real","cost":"I x J -> real","capacity":"I x J -> nonnegative real"},"variables":{"x[i,j]":"nonnegative integer"},"constraints":["forall i in I: sum(j in J, x[i,j]) <= availability[i]","forall j in J: sum(i in I, capacity[i,j]*x[i,j]) >= demand[j]"],"objective":"minimize sum(i in I, j in J, cost[i,j]*x[i,j])"}

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

    model.available_aircraft = pyo.Param(
        model.aircraft_types,
        initialize=lambda mdl, i: availability[i],
        within=pyo.NonNegativeIntegers,
    )
    model.route_demand = pyo.Param(
        model.routes,
        initialize=lambda mdl, j: demand[j],
        within=pyo.NonNegativeReals,
    )
    model.assignment_cost = pyo.Param(
        model.aircraft_types,
        model.routes,
        initialize=lambda mdl, i, j: cost[i][j],
        within=pyo.Reals,
    )
    model.passenger_capacity = pyo.Param(
        model.aircraft_types,
        model.routes,
        initialize=lambda mdl, i, j: capacity[i][j],
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(
        model.aircraft_types,
        model.routes,
        domain=pyo.NonNegativeIntegers,
    )

    def availability_rule(mdl, i):
        return (
            sum(mdl.x[i, j] for j in mdl.routes)
            <= mdl.available_aircraft[i]
        )

    model.availability_limits = pyo.Constraint(
        model.aircraft_types,
        rule=availability_rule,
    )

    def demand_rule(mdl, j):
        return (
            sum(
                mdl.passenger_capacity[i, j] * mdl.x[i, j]
                for i in mdl.aircraft_types
            )
            >= mdl.route_demand[j]
        )

    model.demand_requirements = pyo.Constraint(
        model.routes,
        rule=demand_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[i, j] * model.x[i, j]
            for i in model.aircraft_types
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