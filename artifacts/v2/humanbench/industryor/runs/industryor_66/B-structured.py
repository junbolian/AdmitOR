# IR: {"sets":{"J":"range(len(params['route_cost']))","I":"range(len(unique(params['sales_locations'])))","S[j]":"distinct locations in params['route_locations'][j]"},"params":{"route_cost":"params['route_cost']","route_capacity_r":"params['route_capacity_r']","sales_locations":"required structural input: all sales locations","route_locations":"required structural input: locations on each route, aligned with route_cost"},"variables":{"x[j]":"binary"},"constraints":["For each i in I: sum(x[j] for j in J whose route contains location i) >= 1.","For each j in J: len(S[j])*x[j] <= route_capacity_r."],"objective":"minimize sum(route_cost[j]*x[j] for j in J)","failure_behavior":"Return insufficient_route_data when required route structure is absent; never invent route incidence."}
#
# The stated PARAMS do not identify the locations or route memberships.
# Route costs and a capacity alone cannot determine a covering problem:
# equally priced routes may cover every location or leave some uncovered.
# Consequently, a valid numerical answer requires additional structural data:
#   params["sales_locations"]: iterable of all required location identifiers.
#   params["route_locations"]: iterable of location iterables, one per route.
# If only the two stated parameters are supplied, the problem is
# underdetermined. Changing the previous failure into a numerical objective
# would require inventing information absent from the problem statement.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    route_cost = list(params["route_cost"])
    route_capacity_r = params["route_capacity_r"]

    if (
        "sales_locations" not in params
        or "route_locations" not in params
    ):
        return {"objective": None, "status": "insufficient_route_data"}

    sales_locations = list(dict.fromkeys(params["sales_locations"]))
    route_locations = [
        frozenset(locations)
        for locations in params["route_locations"]
    ]

    if len(route_locations) != len(route_cost):
        return {"objective": None, "status": "invalid_route_data"}

    if route_capacity_r < 0:
        return {"objective": None, "status": "invalid_capacity"}

    location_universe = frozenset(sales_locations)
    if any(
        not locations.issubset(location_universe)
        for locations in route_locations
    ):
        return {"objective": None, "status": "unknown_route_location"}

    covering_routes = {
        location_id: [
            route_id
            for route_id, locations in enumerate(route_locations)
            if location in locations
        ]
        for location_id, location in enumerate(sales_locations)
    }

    model = pyo.ConcreteModel()
    model.route_ids = pyo.Set(
        initialize=range(len(route_cost)),
        ordered=True,
    )
    model.location_ids = pyo.Set(
        initialize=range(len(sales_locations)),
        ordered=True,
    )

    model.route_used = pyo.Var(
        model.route_ids,
        domain=pyo.Binary,
    )

    def coverage_rule(instance, location_id):
        # Tuple form remains valid when the sum has no variable terms.
        return (
            1,
            pyo.quicksum(
                instance.route_used[route_id]
                for route_id in covering_routes[location_id]
            ),
            None,
        )

    model.location_coverage = pyo.Constraint(
        model.location_ids,
        rule=coverage_rule,
    )

    def capacity_rule(instance, route_id):
        return (
            len(route_locations[route_id])
            * instance.route_used[route_id]
            <= route_capacity_r
        )

    model.route_capacity = pyo.Constraint(
        model.route_ids,
        rule=capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            route_cost[route_id] * model.route_used[route_id]
            for route_id in model.route_ids
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