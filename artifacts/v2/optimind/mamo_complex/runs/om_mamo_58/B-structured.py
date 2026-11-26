# IR: {"sets":{"cities":[1,2,3,4],"arcs":"(i,j) in cities x cities where i != j"},"params":{"initial_supplies":"params['initial_supplies'][i-1]","demands":"params['demands'][i-1]","transport_costs":"params['transport_costs'][i-1][j-1]"},"variables":{"ship[i,j]":"nonnegative integer, for each arc"},"constraints":["For each city i: initial_supplies[i] + sum(ship[j,i] for j != i) - sum(ship[i,j] for j != i) >= demands[i]."],"objective":"Minimize sum(transport_costs[i,j] * ship[i,j] for all arcs)."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Redistribute vaccines using four-element vectors and a 4-by-4 cost matrix."""
    model = pyo.ConcreteModel()

    model.cities = pyo.RangeSet(1, 4)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in model.cities
            for destination in model.cities
            if origin != destination
        ],
    )

    model.initial_supply = pyo.Param(
        model.cities,
        initialize={
            city: params["initial_supplies"][city - 1]
            for city in model.cities
        },
        within=pyo.NonNegativeIntegers,
    )
    model.required_supply = pyo.Param(
        model.cities,
        initialize={
            city: params["demands"][city - 1]
            for city in model.cities
        },
        within=pyo.NonNegativeIntegers,
    )
    model.unit_transport_cost = pyo.Param(
        model.arcs,
        initialize={
            (origin, destination):
                params["transport_costs"][origin - 1][destination - 1]
            for origin, destination in model.arcs
        },
        within=pyo.NonNegativeReals,
    )

    model.ship = pyo.Var(model.arcs, domain=pyo.NonNegativeIntegers)

    def demand_coverage_rule(instance, city):
        incoming = sum(
            instance.ship[other, city]
            for other in instance.cities
            if other != city
        )
        outgoing = sum(
            instance.ship[city, other]
            for other in instance.cities
            if other != city
        )
        return (
            instance.initial_supply[city] + incoming - outgoing
            >= instance.required_supply[city]
        )

    model.demand_coverage = pyo.Constraint(
        model.cities, rule=demand_coverage_rule
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_transport_cost[origin, destination]
            * model.ship[origin, destination]
            for origin, destination in model.arcs
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