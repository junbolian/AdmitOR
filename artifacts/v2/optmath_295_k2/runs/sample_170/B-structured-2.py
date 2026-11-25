# IR: {"sets":{"aircraft":[0,1,2,3,4],"routes":[0,1,2,3,4,5]},"params":{"availability":"availability[i], read from params['availability']","demand":"demand[j], read from params['demand']","capability":"capability[i,j], read from params['capability']","cost":"cost[i,j], read from params['cost']"},"variables":{"assignment[i,j]":"nonnegative integer"},"constraints":["For each aircraft i: sum(assignment[i,j] for j in routes) <= availability[i]","For each route j: sum(capability[i,j]*assignment[i,j] for i in aircraft) >= demand[j]"],"objective":"Minimize sum(cost[i,j]*assignment[i,j] for i in aircraft for j in routes)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept vectors/matrices as sequences or mappings keyed by entity names."""
    availability = params["availability"]
    demand = params["demand"]
    capability = params["capability"]
    cost = params["cost"]

    def vector_entry(values, position, prefix):
        if isinstance(values, Mapping):
            label = f"{prefix}_{position}"
            return values[label] if label in values else values[position]
        return values[position]

    def matrix_entry(values, aircraft, route):
        if isinstance(values, Mapping):
            labels = (f"aircraft_{aircraft}", f"route_{route}")
            if labels in values:
                return values[labels]
            if (aircraft, route) in values:
                return values[aircraft, route]
        row = vector_entry(values, aircraft, "aircraft")
        return vector_entry(row, route, "route")

    model = pyo.ConcreteModel()
    model.aircraft = pyo.RangeSet(0, 4)
    model.routes = pyo.RangeSet(0, 5)

    model.availability = pyo.Param(
        model.aircraft,
        initialize=lambda instance, aircraft: vector_entry(
            availability, aircraft, "aircraft"
        ),
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.routes,
        initialize=lambda instance, route: vector_entry(demand, route, "route"),
        within=pyo.NonNegativeReals,
    )
    model.capability = pyo.Param(
        model.aircraft,
        model.routes,
        initialize=lambda instance, aircraft, route: matrix_entry(
            capability, aircraft, route
        ),
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.aircraft,
        model.routes,
        initialize=lambda instance, aircraft, route: matrix_entry(
            cost, aircraft, route
        ),
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(
        model.aircraft,
        model.routes,
        domain=pyo.NonNegativeIntegers,
    )

    def availability_rule(instance, aircraft):
        return (
            sum(
                instance.assignment[aircraft, route]
                for route in instance.routes
            )
            <= instance.availability[aircraft]
        )

    model.availability_limit = pyo.Constraint(
        model.aircraft, rule=availability_rule
    )

    def coverage_rule(instance, route):
        return (
            sum(
                instance.capability[aircraft, route]
                * instance.assignment[aircraft, route]
                for aircraft in instance.aircraft
            )
            >= instance.demand[route]
        )

    model.route_coverage = pyo.Constraint(model.routes, rule=coverage_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[aircraft, route] * model.assignment[aircraft, route]
            for aircraft in model.aircraft
            for route in model.routes
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}