# IR: {"sets":{"I":[0,1,2,3,4],"J":[0,1,2,3,4,5]},"params":{"availability":"I -> nonnegative real","demand":"J -> nonnegative real","capacity":"I x J -> nonnegative real","cost":"I x J -> real"},"variables":{"x[i,j]":"nonnegative integer"},"constraints":["forall i in I: sum(x[i,j] for j in J) <= availability[i]","forall j in J: sum(capacity[i,j]*x[i,j] for i in I) >= demand[j]"],"objective":"minimize sum(cost[i,j]*x[i,j] for i in I for j in J)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept sequences or mappings keyed by aircraft_i and route_j labels."""

    availability_data = params["availability"]
    demand_data = params["demand"]
    capacity_data = params["capacity"]
    cost_data = params["cost"]

    def entry(data, position, label):
        if isinstance(data, Mapping) and label in data:
            return data[label]
        return data[position]

    def matrix_entry(data, aircraft, route):
        row = entry(data, aircraft, f"aircraft_{aircraft}")
        return entry(row, route, f"route_{route}")

    model = pyo.ConcreteModel()
    model.aircraft_types = pyo.RangeSet(0, 4)
    model.routes = pyo.RangeSet(0, 5)

    model.availability = pyo.Param(
        model.aircraft_types,
        initialize=lambda mdl, i: entry(
            availability_data, i, f"aircraft_{i}"
        ),
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.routes,
        initialize=lambda mdl, j: entry(demand_data, j, f"route_{j}"),
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.aircraft_types,
        model.routes,
        initialize=lambda mdl, i, j: matrix_entry(capacity_data, i, j),
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.aircraft_types,
        model.routes,
        initialize=lambda mdl, i, j: matrix_entry(cost_data, i, j),
        within=pyo.Reals,
    )

    model.x = pyo.Var(
        model.aircraft_types,
        model.routes,
        domain=pyo.NonNegativeIntegers,
    )

    def availability_rule(mdl, i):
        return (
            sum(mdl.x[i, j] for j in mdl.routes)
            <= mdl.availability[i]
        )

    model.availability_limits = pyo.Constraint(
        model.aircraft_types, rule=availability_rule
    )

    def demand_rule(mdl, j):
        return (
            sum(
                mdl.capacity[i, j] * mdl.x[i, j]
                for i in mdl.aircraft_types
            )
            >= mdl.demand[j]
        )

    model.route_requirements = pyo.Constraint(
        model.routes, rule=demand_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.x[i, j]
            for i in model.aircraft_types
            for j in model.routes
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # Appsi can raise when no feasible solution can be loaded.
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}