# IR: {"sets":{"O":[0,1,2,3],"D":[0,1,2,3,4],"P":[0,1]},"params":{"input_format":"flat or nested lists/tuples, flattened recursively in the specified order","supply[o,p]":"flatten(params['supply'])[2*o+p]","demand[d,p]":"flatten(params['demand'])[2*d+p]","cost[o,d,p]":"flatten(params['cost'])[10*o+2*d+p]","capacity[o,d]":"flatten(params['capacity'])[5*o+d]"},"variables":{"shipment[o,d,p]":"nonnegative continuous"},"constraints":{"supply_balance[o,p]":"sum(shipment[o,d,p] for d in D) == supply[o,p]","demand_balance[d,p]":"sum(shipment[o,d,p] for o in O) == demand[d,p]","route_capacity[o,d]":"sum(shipment[o,d,p] for p in P) <= capacity[o,d]"},"objective":"minimize sum(cost[o,d,p]*shipment[o,d,p] for o in O for d in D for p in P)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _flatten(values):
    """Flatten flat or nested lists/tuples while preserving input order."""
    flattened = []
    for value in values:
        if isinstance(value, (list, tuple)):
            flattened.extend(_flatten(value))
        else:
            flattened.append(value)
    return flattened


def solve(params):
    supply = _flatten(params["supply"])
    demand = _flatten(params["demand"])
    cost = _flatten(params["cost"])
    capacity = _flatten(params["capacity"])

    if (
        len(supply) != 8
        or len(demand) != 10
        or len(cost) != 40
        or len(capacity) != 20
    ):
        return {"objective": None, "status": "invalid_dimensions"}

    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, 3)
    model.destinations = pyo.RangeSet(0, 4)
    model.products = pyo.RangeSet(0, 1)

    model.supply = pyo.Param(
        model.origins,
        model.products,
        initialize={
            (origin, product): supply[2 * origin + product]
            for origin in model.origins
            for product in model.products
        },
        within=pyo.Reals,
    )

    model.demand = pyo.Param(
        model.destinations,
        model.products,
        initialize={
            (destination, product): demand[2 * destination + product]
            for destination in model.destinations
            for product in model.products
        },
        within=pyo.Reals,
    )

    model.cost = pyo.Param(
        model.origins,
        model.destinations,
        model.products,
        initialize={
            (origin, destination, product): cost[
                10 * origin + 2 * destination + product
            ]
            for origin in model.origins
            for destination in model.destinations
            for product in model.products
        },
        within=pyo.Reals,
    )

    model.capacity = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (origin, destination): capacity[5 * origin + destination]
            for origin in model.origins
            for destination in model.destinations
        },
        within=pyo.Reals,
    )

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        model.products,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(instance, origin, product):
        return (
            sum(
                instance.shipment[origin, destination, product]
                for destination in instance.destinations
            )
            == instance.supply[origin, product]
        )

    model.supply_balance = pyo.Constraint(
        model.origins,
        model.products,
        rule=supply_rule,
    )

    def demand_rule(instance, destination, product):
        return (
            sum(
                instance.shipment[origin, destination, product]
                for origin in instance.origins
            )
            == instance.demand[destination, product]
        )

    model.demand_balance = pyo.Constraint(
        model.destinations,
        model.products,
        rule=demand_rule,
    )

    def capacity_rule(instance, origin, destination):
        return (
            sum(
                instance.shipment[origin, destination, product]
                for product in instance.products
            )
            <= instance.capacity[origin, destination]
        )

    model.route_capacity = pyo.Constraint(
        model.origins,
        model.destinations,
        rule=capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[origin, destination, product]
            * model.shipment[origin, destination, product]
            for origin in model.origins
            for destination in model.destinations
            for product in model.products
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