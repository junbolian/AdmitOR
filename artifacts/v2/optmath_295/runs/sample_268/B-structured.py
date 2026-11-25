# IR: {"sets":{"O":["origin_0","origin_1","origin_2","origin_3","origin_4"],"D":["destination_0","destination_1","destination_2","destination_3","destination_4","destination_5"]},"params":{"warehouse_supply":"O -> nonnegative real, read from params","store_demand":"D -> nonnegative real, read from params","shipping_cost":"O x D -> real, read from params","route_capacity":"O x D -> nonnegative real, read from params"},"variables":{"shipment[o,d]":"nonnegative continuous"},"constraints":["sum(shipment[o,d] for d in D) == warehouse_supply[o], for o in O","sum(shipment[o,d] for o in O) == store_demand[d], for d in D","shipment[o,d] <= route_capacity[o,d], for (o,d) in O x D"],"objective":"minimize sum(shipping_cost[o,d] * shipment[o,d] for (o,d) in O x D)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Supply and demand accept sequences in index order or dictionaries
    keyed by location names or integer indices.

    Costs and capacities accept two-dimensional sequences, nested
    dictionaries, or dictionaries keyed by (origin, destination) tuples.
    """
    warehouse_supply = params["warehouse_supply"]
    store_demand = params["store_demand"]
    shipping_cost = params["shipping_cost"]
    route_capacity = params["route_capacity"]

    origins = [f"origin_{idx}" for idx in range(5)]
    destinations = [f"destination_{idx}" for idx in range(6)]

    def indexed_value(data, label, position):
        if isinstance(data, Mapping):
            if label in data:
                return data[label]
            return data[position]
        return data[position]

    def route_value(data, origin, destination, origin_idx, destination_idx):
        if isinstance(data, Mapping):
            if (origin, destination) in data:
                return data[(origin, destination)]
            if (origin_idx, destination_idx) in data:
                return data[(origin_idx, destination_idx)]
        row = indexed_value(data, origin, origin_idx)
        return indexed_value(row, destination, destination_idx)

    model = pyo.ConcreteModel()

    model.origins = pyo.Set(initialize=origins, ordered=True)
    model.destinations = pyo.Set(initialize=destinations, ordered=True)

    model.warehouse_supply = pyo.Param(
        model.origins,
        initialize={
            origin: indexed_value(warehouse_supply, origin, origin_idx)
            for origin_idx, origin in enumerate(origins)
        },
        within=pyo.NonNegativeReals,
    )

    model.store_demand = pyo.Param(
        model.destinations,
        initialize={
            destination: indexed_value(
                store_demand, destination, destination_idx
            )
            for destination_idx, destination in enumerate(destinations)
        },
        within=pyo.NonNegativeReals,
    )

    model.shipping_cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (origin, destination): route_value(
                shipping_cost,
                origin,
                destination,
                origin_idx,
                destination_idx,
            )
            for origin_idx, origin in enumerate(origins)
            for destination_idx, destination in enumerate(destinations)
        },
        within=pyo.Reals,
    )

    model.route_capacity = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (origin, destination): route_value(
                route_capacity,
                origin,
                destination,
                origin_idx,
                destination_idx,
            )
            for origin_idx, origin in enumerate(origins)
            for destination_idx, destination in enumerate(destinations)
        },
        within=pyo.NonNegativeReals,
    )

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(instance, origin):
        return (
            sum(
                instance.shipment[origin, destination]
                for destination in instance.destinations
            )
            == instance.warehouse_supply[origin]
        )

    def demand_rule(instance, destination):
        return (
            sum(
                instance.shipment[origin, destination]
                for origin in instance.origins
            )
            == instance.store_demand[destination]
        )

    def capacity_rule(instance, origin, destination):
        return (
            instance.shipment[origin, destination]
            <= instance.route_capacity[origin, destination]
        )

    model.supply_balance = pyo.Constraint(
        model.origins, rule=supply_rule
    )
    model.demand_balance = pyo.Constraint(
        model.destinations, rule=demand_rule
    )
    model.route_capacity_limit = pyo.Constraint(
        model.origins, model.destinations, rule=capacity_rule
    )

    model.total_shipping_cost = pyo.Objective(
        expr=sum(
            model.shipping_cost[origin, destination]
            * model.shipment[origin, destination]
            for origin in model.origins
            for destination in model.destinations
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_shipping_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}