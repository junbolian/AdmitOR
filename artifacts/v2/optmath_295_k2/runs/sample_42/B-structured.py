# IR: {"sets":{"P":[0,1],"O":[0,1,2,3],"D":[0,1,2,3,4]},"params":{"cost":"params['cost'], normalized to [p,o,d] by axis sizes","supply":"params['supply'], normalized to [p,o] by axis sizes","demand":"params['demand'], normalized to [p,d] by axis sizes","capacity":"params['capacity'], normalized to [o,d] by axis sizes"},"variables":{"ship[p,o,d]":"NonNegativeReals"},"constraints":["sum(ship[p,o,d] for d in D) == supply[p,o] for p in P,o in O","sum(ship[p,o,d] for o in O) == demand[p,d] for p in P,d in D","sum(ship[p,o,d] for p in P) <= capacity[o,d] for o in O,d in D"],"objective":"minimize sum(cost[p,o,d]*ship[p,o,d] for p in P,o in O,d in D)"}

from collections.abc import Mapping
from itertools import product

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _normalize(data, expected_shape):
    """Normalize nested data or tuple-keyed mappings to canonical axis order.

    Axis lengths identify products, origins, and destinations uniquely.
    For example, cost accepts both [product][origin][destination] and
    [origin][destination][product], as well as other axis permutations.
    All indices must be zero-based.
    """
    dimensions = len(expected_shape)
    tuple_keyed = (
        isinstance(data, Mapping)
        and bool(data)
        and isinstance(next(iter(data)), tuple)
    )

    if tuple_keyed:
        keys = list(data)
        if any(
            not isinstance(key, tuple) or len(key) != dimensions
            for key in keys
        ):
            raise ValueError("Parameter mapping has inconsistent tuple keys.")

        axis_indices = [
            {key[axis] for key in keys}
            for axis in range(dimensions)
        ]
        observed_shape = tuple(len(indices) for indices in axis_indices)

        if any(
            indices != set(range(len(indices)))
            for indices in axis_indices
        ):
            raise ValueError("Parameter indices must be contiguous and zero-based.")
    else:
        observed_lengths = []
        current = data
        for axis in range(dimensions):
            observed_lengths.append(len(current))
            if axis < dimensions - 1:
                current = current[0]
        observed_shape = tuple(observed_lengths)

    if sorted(observed_shape) != sorted(expected_shape):
        raise ValueError(
            f"Parameter shape {observed_shape} does not match any "
            f"axis permutation of {expected_shape}."
        )

    # For each input axis, identify the corresponding canonical axis.
    input_axis_order = tuple(
        expected_shape.index(length) for length in observed_shape
    )

    normalized = {}
    for canonical_indices in product(
        *(range(length) for length in expected_shape)
    ):
        input_indices = tuple(
            canonical_indices[axis] for axis in input_axis_order
        )

        if tuple_keyed:
            value = data[input_indices]
        else:
            value = data
            for position in input_indices:
                value = value[position]

        normalized[canonical_indices] = value

    return normalized


def solve(params):
    cost = _normalize(params["cost"], (2, 4, 5))
    supply = _normalize(params["supply"], (2, 4))
    demand = _normalize(params["demand"], (2, 5))
    capacity = _normalize(params["capacity"], (4, 5))

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, 1)
    model.O = pyo.RangeSet(0, 3)
    model.D = pyo.RangeSet(0, 4)

    model.transport_cost = pyo.Param(
        model.P,
        model.O,
        model.D,
        initialize=cost,
        within=pyo.Reals,
    )
    model.available_supply = pyo.Param(
        model.P,
        model.O,
        initialize=supply,
        within=pyo.NonNegativeReals,
    )
    model.required_demand = pyo.Param(
        model.P,
        model.D,
        initialize=demand,
        within=pyo.NonNegativeReals,
    )
    model.route_capacity = pyo.Param(
        model.O,
        model.D,
        initialize=capacity,
        within=pyo.NonNegativeReals,
    )

    model.ship = pyo.Var(
        model.P,
        model.O,
        model.D,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(mdl, product_id, origin):
        return (
            sum(
                mdl.ship[product_id, origin, destination]
                for destination in mdl.D
            )
            == mdl.available_supply[product_id, origin]
        )

    model.supply_balance = pyo.Constraint(
        model.P, model.O, rule=supply_rule
    )

    def demand_rule(mdl, product_id, destination):
        return (
            sum(
                mdl.ship[product_id, origin, destination]
                for origin in mdl.O
            )
            == mdl.required_demand[product_id, destination]
        )

    model.demand_balance = pyo.Constraint(
        model.P, model.D, rule=demand_rule
    )

    def capacity_rule(mdl, origin, destination):
        return (
            sum(
                mdl.ship[product_id, origin, destination]
                for product_id in mdl.P
            )
            <= mdl.route_capacity[origin, destination]
        )

    model.capacity_limit = pyo.Constraint(
        model.O, model.D, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[product_id, origin, destination]
            * model.ship[product_id, origin, destination]
            for product_id in model.P
            for origin in model.O
            for destination in model.D
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