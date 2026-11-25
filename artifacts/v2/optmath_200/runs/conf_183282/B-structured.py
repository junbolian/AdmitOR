# IR: {"sets":{"O":[0,1,2,3],"D":[0,1,2,3,4],"P":[0,1]},"params":{"supply":"nonnegative real[O,P] from params['supply']","demand":"nonnegative real[D,P] from params['demand']","cost":"real[O,D,P] from params['cost']","transport_capacity":"nonnegative real[O,D] from params['transport_capacity']"},"variables":{"shipment[O,D,P]":"continuous nonnegative real"},"constraints":["sum(d in D, shipment[o,d,p]) = supply[o,p] for each o,p","sum(o in O, shipment[o,d,p]) = demand[d,p] for each d,p","sum(p in P, shipment[o,d,p]) <= transport_capacity[o,d] for each o,d"],"objective":"minimize sum(o in O,d in D,p in P, cost[o,d,p]*shipment[o,d,p])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using nested arrays or dictionaries keyed by index tuples."""

    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    transport_capacity = params["transport_capacity"]

    def indexed_value(data, *indices):
        if isinstance(data, dict) and indices in data:
            return data[indices]
        value = data
        for idx in indices:
            value = value[idx]
        return value

    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, 3)
    model.destinations = pyo.RangeSet(0, 4)
    model.products = pyo.RangeSet(0, 1)

    model.supply = pyo.Param(
        model.origins,
        model.products,
        initialize=lambda mdl, origin, product: indexed_value(
            supply, origin, product
        ),
        within=pyo.NonNegativeReals,
    )

    model.demand = pyo.Param(
        model.destinations,
        model.products,
        initialize=lambda mdl, destination, product: indexed_value(
            demand, destination, product
        ),
        within=pyo.NonNegativeReals,
    )

    model.cost = pyo.Param(
        model.origins,
        model.destinations,
        model.products,
        initialize=lambda mdl, origin, destination, product: indexed_value(
            cost, origin, destination, product
        ),
        within=pyo.Reals,
    )

    model.transport_capacity = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, origin, destination: indexed_value(
            transport_capacity, origin, destination
        ),
        within=pyo.NonNegativeReals,
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
            <= mdl.transport_capacity[origin, destination]
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
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}