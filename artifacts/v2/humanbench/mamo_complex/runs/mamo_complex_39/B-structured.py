# IR: {"sets":{"D":[1,2,3,4],"A":"{(i,j) in D x D: i != j}"},"params":{"supply":"D -> nonnegative real","demand":"D -> nonnegative real","cost_i_to_j":"nonnegative real for each (i,j) in A"},"variables":{"shipment[i,j]":"nonnegative real for (i,j) in A","unused[i]":"nonnegative real, bounded above by supply[i], for i in D"},"constraints":["For each i: supply[i] - unused[i] + sum(shipment[j,i] for j != i) - sum(shipment[i,j] for j != i) = demand[i]"],"objective":"minimize sum(cost_i_to_j * shipment[i,j] for (i,j) in A)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _district_values(values):
    """Accept four-element sequences or mappings keyed by district."""
    districts = (1, 2, 3, 4)

    if isinstance(values, Mapping):
        key_options = (
            tuple(f"D{district}" for district in districts),
            districts,
            tuple(str(district) for district in districts),
            tuple(district - 1 for district in districts),
        )
        for keys in key_options:
            if all(key in values for key in keys):
                return {
                    district: values[key]
                    for district, key in zip(districts, keys)
                }
        raise ValueError("Supply and demand mappings must identify all four districts.")

    if len(values) != len(districts):
        raise ValueError("Supply and demand sequences must each contain four values.")

    return {
        district: values[district - 1]
        for district in districts
    }


def solve(params):
    supply_data = _district_values(params["supply"])
    demand_data = _district_values(params["demand"])
    cost_data = {
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
    model.districts = pyo.Set(initialize=(1, 2, 3, 4), ordered=True)
    model.routes = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in model.districts
            for destination in model.districts
            if origin != destination
        ],
    )

    model.food_supply = pyo.Param(
        model.districts,
        initialize=supply_data,
        within=pyo.NonNegativeReals,
    )
    model.food_demand = pyo.Param(
        model.districts,
        initialize=demand_data,
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.routes,
        initialize=cost_data,
        within=pyo.NonNegativeReals,
    )

    model.shipment = pyo.Var(
        model.routes,
        domain=pyo.NonNegativeReals,
    )

    # Supply is available inventory; excess may remain outside the allocation.
    # Each district's allocated food after transfers equals its demand exactly.
    def unused_bounds(instance, district):
        return (0, instance.food_supply[district])

    model.unused = pyo.Var(
        model.districts,
        domain=pyo.NonNegativeReals,
        bounds=unused_bounds,
    )

    def food_balance_rule(instance, district):
        incoming = sum(
            instance.shipment[origin, district]
            for origin in instance.districts
            if origin != district
        )
        outgoing = sum(
            instance.shipment[district, destination]
            for destination in instance.districts
            if destination != district
        )
        return (
            instance.food_supply[district]
            - instance.unused[district]
            + incoming
            - outgoing
            == instance.food_demand[district]
        )

    model.food_balance = pyo.Constraint(
        model.districts,
        rule=food_balance_rule,
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[origin, destination]
            * model.shipment[origin, destination]
            for origin, destination in model.routes
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