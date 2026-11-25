# IR: {"sets":{"P":[0,1],"O":[0,1,2,3],"D":[0,1,2,3,4]},"params":{"cost[P,O,D]":"real; params['cost']; accepts P-O-D, O-D-P, or O-P-D indexing","supply[P,O]":"nonnegative real; params['supply']; accepts P-O or O-P indexing","demand[P,D]":"nonnegative real; params['demand']; accepts P-D or D-P indexing","capacity[O,D]":"nonnegative real; params['capacity']; O-D indexing"},"variables":{"ship[P,O,D]":"nonnegative continuous"},"constraints":["For each p,o: sum_d ship[p,o,d] = supply[p,o]","For each p,d: sum_o ship[p,o,d] = demand[p,d]","For each o,d: sum_p ship[p,o,d] <= capacity[o,d]"],"objective":"minimize sum_{p,o,d} cost[p,o,d] * ship[p,o,d]"}
from collections.abc import Mapping
from itertools import product

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _entry(data, indices):
    """Read a tuple-keyed mapping or nested sequences/mappings."""
    if isinstance(data, Mapping) and indices in data:
        return data[indices]

    value = data
    for idx in indices:
        value = value[idx]
    return value


def _normalize(data, dimensions, axis_orders, parameter_name):
    """Convert supported input layouts to canonical tuple-keyed data.

    Each axis order specifies the input axes using canonical axis positions.
    For example, (1, 2, 0) converts O-D-P input to canonical P-O-D keys.
    """
    canonical_keys = tuple(product(*(range(size) for size in dimensions)))

    for axis_order in axis_orders:
        normalized = {}
        try:
            for key in canonical_keys:
                input_key = tuple(key[axis] for axis in axis_order)
                normalized[key] = _entry(data, input_key)
        except (IndexError, KeyError, TypeError):
            continue
        return normalized

    raise ValueError(
        f"Unsupported shape or missing indices for parameter "
        f"'{parameter_name}'."
    )


def solve(params):
    """
    Solve the continuous two-product transportation problem.

    Supported nested-array layouts:
        cost:     [product][origin][destination],
                  [origin][destination][product], or
                  [origin][product][destination]
        supply:   [product][origin] or [origin][product]
        demand:   [product][destination] or [destination][product]
        capacity: [origin][destination]

    Nested mappings and tuple-keyed mappings support the same layouts.
    """
    cost_data = _normalize(
        params["cost"],
        dimensions=(2, 4, 5),
        axis_orders=((0, 1, 2), (1, 2, 0), (1, 0, 2)),
        parameter_name="cost",
    )
    supply_data = _normalize(
        params["supply"],
        dimensions=(2, 4),
        axis_orders=((0, 1), (1, 0)),
        parameter_name="supply",
    )
    demand_data = _normalize(
        params["demand"],
        dimensions=(2, 5),
        axis_orders=((0, 1), (1, 0)),
        parameter_name="demand",
    )
    capacity_data = _normalize(
        params["capacity"],
        dimensions=(4, 5),
        axis_orders=((0, 1),),
        parameter_name="capacity",
    )

    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 1)
    model.origins = pyo.RangeSet(0, 3)
    model.destinations = pyo.RangeSet(0, 4)

    model.cost = pyo.Param(
        model.products,
        model.origins,
        model.destinations,
        initialize=cost_data,
        within=pyo.Reals,
    )
    model.supply = pyo.Param(
        model.products,
        model.origins,
        initialize=supply_data,
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.products,
        model.destinations,
        initialize=demand_data,
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.origins,
        model.destinations,
        initialize=capacity_data,
        within=pyo.NonNegativeReals,
    )

    model.ship = pyo.Var(
        model.products,
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(mdl, p, o):
        return (
            sum(mdl.ship[p, o, d] for d in mdl.destinations)
            == mdl.supply[p, o]
        )

    model.supply_balance = pyo.Constraint(
        model.products,
        model.origins,
        rule=supply_rule,
    )

    def demand_rule(mdl, p, d):
        return (
            sum(mdl.ship[p, o, d] for o in mdl.origins)
            == mdl.demand[p, d]
        )

    model.demand_balance = pyo.Constraint(
        model.products,
        model.destinations,
        rule=demand_rule,
    )

    def capacity_rule(mdl, o, d):
        return (
            sum(mdl.ship[p, o, d] for p in mdl.products)
            <= mdl.capacity[o, d]
        )

    model.route_capacity = pyo.Constraint(
        model.origins,
        model.destinations,
        rule=capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[p, o, d] * model.ship[p, o, d]
            for p in model.products
            for o in model.origins
            for d in model.destinations
        ),
        sense=pyo.minimize,
    )

    solve_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        solve_failed = True

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {
            "objective": None,
            "status": "solve_failed" if solve_failed else "objective_unavailable",
        }

    return {"objective": obj_val, "status": "optimal"}