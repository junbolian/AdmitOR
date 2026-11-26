# IR: {"sets":{"H":"{1,...,7}","A":"{(i,j) in H x H: i != j}"},"params":{"initial_stock":"H -> nonnegative real","required_supplies":"H -> nonnegative real","transfer_costs":"A -> nonnegative real"},"variables":{"transfer[i,j]":"nonnegative real for (i,j) in A"},"constraints":["For each i in H: initial_stock[i] + sum(transfer[j,i] for j != i) - sum(transfer[i,j] for j != i) >= required_supplies[i]"],"objective":"Minimize sum(transfer_costs[i,j] * transfer[i,j] for (i,j) in A)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Input formats:
      initial_stock, required_supplies:
        - Seven-element sequences in hospital order; or
        - Mappings keyed by hospital numbers 1 through 7.

      transfer_costs:
        - A 7-by-7 nested sequence (diagonal entries are ignored);
        - A nested mapping keyed by hospital numbers 1 through 7; or
        - A mapping keyed by ordered pairs (i, j), i != j.

    Transfers may pass through intermediate hospitals.
    """
    stock_data = params["initial_stock"]
    required_data = params["required_supplies"]
    cost_data = params["transfer_costs"]

    def hospital_value(data, hospital):
        if isinstance(data, Mapping):
            return data[hospital]
        return data[hospital - 1]

    def route_cost(origin, destination):
        if isinstance(cost_data, Mapping):
            if (origin, destination) in cost_data:
                return cost_data[(origin, destination)]
            row = cost_data[origin]
        else:
            row = cost_data[origin - 1]
        return hospital_value(row, destination)

    model = pyo.ConcreteModel()

    model.hospitals = pyo.RangeSet(1, 7)
    model.routes = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in model.hospitals
            for destination in model.hospitals
            if origin != destination
        ],
    )

    model.initial_supply = pyo.Param(
        model.hospitals,
        initialize={
            hospital: hospital_value(stock_data, hospital)
            for hospital in model.hospitals
        },
        within=pyo.NonNegativeReals,
    )
    model.required_supply = pyo.Param(
        model.hospitals,
        initialize={
            hospital: hospital_value(required_data, hospital)
            for hospital in model.hospitals
        },
        within=pyo.NonNegativeReals,
    )
    model.unit_transfer_cost = pyo.Param(
        model.routes,
        initialize={
            (origin, destination): route_cost(origin, destination)
            for origin, destination in model.routes
        },
        within=pyo.NonNegativeReals,
    )

    model.transfer = pyo.Var(
        model.routes,
        domain=pyo.NonNegativeReals,
    )

    def supply_balance_rule(instance, hospital):
        incoming = sum(
            instance.transfer[other, hospital]
            for other in instance.hospitals
            if other != hospital
        )
        outgoing = sum(
            instance.transfer[hospital, other]
            for other in instance.hospitals
            if other != hospital
        )
        return (
            instance.initial_supply[hospital] + incoming - outgoing
            >= instance.required_supply[hospital]
        )

    model.supply_balance = pyo.Constraint(
        model.hospitals,
        rule=supply_balance_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_transfer_cost[origin, destination]
            * model.transfer[origin, destination]
            for origin, destination in model.routes
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}