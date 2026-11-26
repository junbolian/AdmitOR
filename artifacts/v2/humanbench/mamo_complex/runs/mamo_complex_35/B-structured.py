# IR: {"sets":{"cities":[1,2,3,4],"arcs":"ordered city pairs (i,j) with i != j"},"params":{"supply":"params['supply'], sequence in city order","demand":"params['demand'], sequence in city order","cost":"params['cost_i_to_j'] for each arc (i,j)"},"variables":{"shipment[i,j]":"nonnegative integer"},"constraints":["supply[i] + sum(shipment[j,i] for j != i) - sum(shipment[i,j] for j != i) >= demand[i], for each city i"],"objective":"minimize sum(cost[i,j] * shipment[i,j] for all arcs)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Supply and demand must be sequences ordered City 1 through City 4."""
    cities = (1, 2, 3, 4)
    arcs = tuple(
        (origin, destination)
        for origin in cities
        for destination in cities
        if origin != destination
    )

    supply = params["supply"]
    demand = params["demand"]
    costs = {
        (1, 2): params["cost_1_to_2"],
        (1, 3): params["cost_1_to_3"],
        (1, 4): params["cost_1_to_4"],
        (2, 1): params["cost_2_to_1"],
        (2, 3): params["cost_2_to_3"],
        (2, 4): params["cost_2_to_4"],
        (3, 1): params["cost_3_to_1"],
        (3, 2): params["cost_3_to_2"],
        (3, 4): params["cost_3_to_4"],
        (4, 1): params["cost_4_to_1"],
        (4, 2): params["cost_4_to_2"],
        (4, 3): params["cost_4_to_3"],
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    model.initial_supply = pyo.Param(
        model.cities,
        initialize={city: supply[city - 1] for city in cities},
        within=pyo.NonNegativeReals,
    )
    model.required_demand = pyo.Param(
        model.cities,
        initialize={city: demand[city - 1] for city in cities},
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.arcs,
        initialize=costs,
        within=pyo.Reals,
    )
    model.shipment = pyo.Var(model.arcs, domain=pyo.NonNegativeIntegers)

    def demand_coverage_rule(instance, city):
        incoming = sum(
            instance.shipment[other, city]
            for other in instance.cities
            if other != city
        )
        outgoing = sum(
            instance.shipment[city, other]
            for other in instance.cities
            if other != city
        )
        return (
            instance.initial_supply[city] + incoming - outgoing
            >= instance.required_demand[city]
        )

    model.demand_coverage = pyo.Constraint(
        model.cities, rule=demand_coverage_rule
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[origin, destination]
            * model.shipment[origin, destination]
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