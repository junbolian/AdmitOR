# IR: {"sets":{"H":[0,1,2,3],"A":"{(i,j) in H x H: i != j}"},"params":{"supply":"nonnegative vector from params['supply']","demand":"nonnegative vector from params['demand']","cost":"nonnegative directed matrix from params['cost']; diagonal unused"},"variables":{"transfer[i,j]":"NonNegativeReals for (i,j) in A"},"constraints":["For each i in H: supply[i] + sum(transfer[j,i] for j != i) - sum(transfer[i,j] for j != i) >= demand[i]"],"objective":"minimize sum(cost[i,j] * transfer[i,j] for (i,j) in A)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _entry(data, position):
    """Accept sequences or mappings keyed by H1..H4 or hospital numbers."""
    if not isinstance(data, Mapping):
        return data[position]

    hospital_label = f"H{position + 1}"
    if hospital_label in data:
        return data[hospital_label]

    # Numeric mappings may use either zero-based or one-based keys.
    if 0 in data:
        return data[position]
    if "0" in data:
        return data[str(position)]

    if position + 1 in data:
        return data[position + 1]
    return data[str(position + 1)]


def solve(params):
    supply_data = params["supply"]
    demand_data = params["demand"]
    cost_data = params["cost"]

    hospitals = tuple(range(4))
    arcs = tuple(
        (origin, destination)
        for origin in hospitals
        for destination in hospitals
        if origin != destination
    )

    model = pyo.ConcreteModel()
    model.H = pyo.Set(initialize=hospitals, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.supply = pyo.Param(
        model.H,
        initialize={
            hospital: _entry(supply_data, hospital)
            for hospital in hospitals
        },
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.H,
        initialize={
            hospital: _entry(demand_data, hospital)
            for hospital in hospitals
        },
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.A,
        initialize={
            (origin, destination): _entry(
                _entry(cost_data, origin), destination
            )
            for origin, destination in arcs
        },
        within=pyo.NonNegativeReals,
    )

    model.transfer = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    def supply_balance_rule(instance, hospital):
        incoming = sum(
            instance.transfer[other, hospital]
            for other in instance.H
            if other != hospital
        )
        outgoing = sum(
            instance.transfer[hospital, other]
            for other in instance.H
            if other != hospital
        )
        return (
            instance.supply[hospital] + incoming - outgoing
            >= instance.demand[hospital]
        )

    model.supply_balance = pyo.Constraint(
        model.H, rule=supply_balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[origin, destination]
            * model.transfer[origin, destination]
            for origin, destination in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}