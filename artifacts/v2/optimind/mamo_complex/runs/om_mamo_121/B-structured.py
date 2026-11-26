# IR: {"sets":{"R":"1..6","A":"{(i,j) in R x R: i != j}"},"params":{"initial_food":"params['initial_food']; region-keyed mapping or sequence in region order","required_food":"params['required_food']; region-keyed mapping or sequence in region order","transport_cost":"params['transport_cost'][i-1][j-1] for (i,j) in A"},"variables":{"shipment[i,j]":"continuous, nonnegative tons for (i,j) in A"},"constraints":["For each i in R: initial_food[i] + sum(shipment[j,i] for j != i) - sum(shipment[i,j] for j != i) >= required_food[i]"],"objective":"Minimize sum(transport_cost[i,j] * shipment[i,j] for (i,j) in A)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _region_value(values, region):
    """Mappings use region keys 1..6; sequences use positions 0..5."""
    if isinstance(values, Mapping):
        return values[region]
    return values[region - 1]


def solve(params):
    initial_food = params["initial_food"]
    required_food = params["required_food"]
    transport_cost = params["transport_cost"]

    model = pyo.ConcreteModel()
    model.regions = pyo.RangeSet(1, 6)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in model.regions
            for destination in model.regions
            if origin != destination
        ],
    )

    model.food_available = pyo.Param(
        model.regions,
        initialize={
            region: _region_value(initial_food, region)
            for region in model.regions
        },
    )
    model.food_required = pyo.Param(
        model.regions,
        initialize={
            region: _region_value(required_food, region)
            for region in model.regions
        },
    )
    model.shipping_cost = pyo.Param(
        model.arcs,
        initialize={
            (origin, destination): transport_cost[origin - 1][destination - 1]
            for origin, destination in model.arcs
        },
    )
    model.shipment = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def food_balance_rule(current_model, region):
        incoming = sum(
            current_model.shipment[other, region]
            for other in current_model.regions
            if other != region
        )
        outgoing = sum(
            current_model.shipment[region, other]
            for other in current_model.regions
            if other != region
        )
        return (
            current_model.food_available[region] + incoming - outgoing
            >= current_model.food_required[region]
        )

    model.food_balance = pyo.Constraint(
        model.regions,
        rule=food_balance_rule,
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.shipping_cost[origin, destination]
            * model.shipment[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    failure_reason = "objective_unavailable"
    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when it cannot load a feasible solution.
        # Objective retrieval below remains the sole success criterion.
        failure_reason = "solver_failed"

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": failure_reason}

    return {"objective": obj_val, "status": "optimal"}