# IR: {"sets":{"O":[0,1,2,3],"D":[0,1,2,3,4],"P":[0,1]},"params":{"supply":"8 values, flat or nested, origin/product order","demand":"10 values, flat or nested, destination/product order","cost":"40 values, flat or nested, origin/destination/product order","capacity":"20 values, flat or nested, origin/destination order"},"variables":{"shipment[o,d,p]":"NonNegativeReals"},"constraints":["forall o,p: sum_d shipment[o,d,p] = supply[o,p]","forall d,p: sum_o shipment[o,d,p] = demand[d,p]","forall o,d: sum_p shipment[o,d,p] <= capacity[o,d]"],"objective":"minimize sum_o,d,p cost[o,d,p]*shipment[o,d,p]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _flatten(values):
    """Flatten JSON arrays in their existing origin-major order."""
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

    for parameter_name, values, expected_count in (
        ("supply", supply, 4 * 2),
        ("demand", demand, 5 * 2),
        ("cost", cost, 4 * 5 * 2),
        ("capacity", capacity, 4 * 5),
    ):
        if len(values) != expected_count:
            return {
                "objective": None,
                "status": "invalid_" + parameter_name + "_shape",
            }

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, 3)
    model.destinations = pyo.RangeSet(0, 4)
    model.products = pyo.RangeSet(0, 1)

    model.supply = pyo.Param(
        model.origins,
        model.products,
        initialize={
            (origin, product): supply[origin * 2 + product]
            for origin in model.origins
            for product in model.products
        },
    )
    model.demand = pyo.Param(
        model.destinations,
        model.products,
        initialize={
            (destination, product): demand[destination * 2 + product]
            for destination in model.destinations
            for product in model.products
        },
    )
    model.cost = pyo.Param(
        model.origins,
        model.destinations,
        model.products,
        initialize={
            (origin, destination, product):
                cost[(origin * 5 + destination) * 2 + product]
            for origin in model.origins
            for destination in model.destinations
            for product in model.products
        },
    )
    model.capacity = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (origin, destination): capacity[origin * 5 + destination]
            for origin in model.origins
            for destination in model.destinations
        },
    )

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        model.products,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(mdl, origin, product):
        return (
            sum(
                mdl.shipment[origin, destination, product]
                for destination in mdl.destinations
            )
            == mdl.supply[origin, product]
        )

    model.supply_balance = pyo.Constraint(
        model.origins, model.products, rule=supply_rule
    )

    def demand_rule(mdl, destination, product):
        return (
            sum(
                mdl.shipment[origin, destination, product]
                for origin in mdl.origins
            )
            == mdl.demand[destination, product]
        )

    model.demand_balance = pyo.Constraint(
        model.destinations, model.products, rule=demand_rule
    )

    def capacity_rule(mdl, origin, destination):
        return (
            sum(
                mdl.shipment[origin, destination, product]
                for product in mdl.products
            )
            <= mdl.capacity[origin, destination]
        )

    model.route_capacity = pyo.Constraint(
        model.origins, model.destinations, rule=capacity_rule
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
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}