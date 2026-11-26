# IR: {"sets":{"R":[1,2,3,4,5,6,7],"A":"{(i,j) in R x R: i != j}"},"params":{"initial_supply":"nonnegative supply indexed by R","demand":"nonnegative requirement indexed by R","transport_cost":"nonnegative directed unit cost indexed by A"},"variables":{"shipment[i,j]":"continuous nonnegative, (i,j) in A"},"constraints":["initial_supply[r] + sum(shipment[i,r] for i != r) - sum(shipment[r,j] for j != r) >= demand[r], for each r in R"],"objective":"minimize sum(transport_cost[i,j] * shipment[i,j] for (i,j) in A)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _region_value(data, region):
    """Read a seven-element sequence or a zero-/one-based indexed mapping."""
    if isinstance(data, Mapping):
        zero_based = 0 in data or "0" in data
        key = region - 1 if zero_based else region
        return data[key] if key in data else data[str(key)]
    return data[region - 1]


def _transport_value(data, origin, destination):
    """
    Accept a nested matrix, or a mapping keyed by (origin, destination).

    Nested sequences may contain seven columns, including the diagonal,
    or six columns with the diagonal omitted. Tuple-key mappings use
    one-based region numbers.
    """
    if isinstance(data, Mapping):
        pair = (origin, destination)
        if pair in data:
            return data[pair]

    row = _region_value(data, origin)
    if isinstance(row, Mapping):
        return _region_value(row, destination)

    if len(row) == 7:
        return row[destination - 1]
    if len(row) == 6:
        column = destination - 1 if destination < origin else destination - 2
        return row[column]
    raise ValueError("Each transport-cost row must contain six or seven entries.")


def solve(params):
    supply_data = params["initial_supply"]
    demand_data = params["demand"]
    cost_data = params["transport_cost"]

    model = pyo.ConcreteModel()
    model.regions = pyo.RangeSet(1, 7)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in model.regions
            for destination in model.regions
            if origin != destination
        ],
    )

    model.supply_amount = pyo.Param(
        model.regions,
        initialize={
            region: _region_value(supply_data, region)
            for region in model.regions
        },
        within=pyo.NonNegativeReals,
    )
    model.required_amount = pyo.Param(
        model.regions,
        initialize={
            region: _region_value(demand_data, region)
            for region in model.regions
        },
        within=pyo.NonNegativeReals,
    )
    model.unit_cost = pyo.Param(
        model.arcs,
        initialize={
            (origin, destination): _transport_value(
                cost_data, origin, destination
            )
            for origin, destination in model.arcs
        },
        within=pyo.NonNegativeReals,
    )

    model.shipment = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def supply_balance_rule(instance, region):
        incoming = sum(
            instance.shipment[origin, region]
            for origin in instance.regions
            if origin != region
        )
        outgoing = sum(
            instance.shipment[region, destination]
            for destination in instance.regions
            if destination != region
        )
        return (
            instance.supply_amount[region] + incoming - outgoing
            >= instance.required_amount[region]
        )

    model.supply_balance = pyo.Constraint(
        model.regions, rule=supply_balance_rule
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[origin, destination]
            * model.shipment[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this error when it cannot load a feasible solution.
        # Let unrelated runtime errors propagate.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}