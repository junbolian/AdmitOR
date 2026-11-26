# IR: {"sets":{"H":[1,2,3,4],"A":"{(i,j) in H x H: i != j}"},"params":{"supply":"H -> nonnegative real","demand":"H -> nonnegative real","cost_1_2":"real","cost_1_3":"real","cost_1_4":"real","cost_2_1":"real","cost_2_3":"real","cost_2_4":"real","cost_3_1":"real","cost_3_2":"real","cost_3_4":"real","cost_4_1":"real","cost_4_2":"real","cost_4_3":"real"},"variables":{"transfer[i,j]":"nonnegative real for (i,j) in A"},"constraints":{"hospital_balance[i]":"supply[i] + sum(transfer[j,i] for j != i) - sum(transfer[i,j] for j != i) >= demand[i], for i in H"},"objective":"minimize sum(cost[i,j] * transfer[i,j] for (i,j) in A)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Supply and demand accept four-element sequences or mappings keyed
    by H1..H4, integers 1..4, or strings '1'..'4'.
    """

    def hospital_value(values, hospital):
        if isinstance(values, Mapping):
            label = f"H{hospital}"
            if label in values:
                return values[label]
            if hospital in values:
                return values[hospital]
            return values[str(hospital)]
        return values[hospital - 1]

    supply_data = params["supply"]
    demand_data = params["demand"]
    cost_data = {
        (1, 2): params["cost_1_2"],
        (1, 3): params["cost_1_3"],
        (1, 4): params["cost_1_4"],
        (2, 1): params["cost_2_1"],
        (2, 3): params["cost_2_3"],
        (2, 4): params["cost_2_4"],
        (3, 1): params["cost_3_1"],
        (3, 2): params["cost_3_2"],
        (3, 4): params["cost_3_4"],
        (4, 1): params["cost_4_1"],
        (4, 2): params["cost_4_2"],
        (4, 3): params["cost_4_3"],
    }

    model = pyo.ConcreteModel()
    model.hospitals = pyo.Set(initialize=[1, 2, 3, 4], ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in model.hospitals
            for destination in model.hospitals
            if origin != destination
        ],
    )

    model.supply = pyo.Param(
        model.hospitals,
        initialize={
            hospital: hospital_value(supply_data, hospital)
            for hospital in model.hospitals
        },
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.hospitals,
        initialize={
            hospital: hospital_value(demand_data, hospital)
            for hospital in model.hospitals
        },
        within=pyo.NonNegativeReals,
    )
    model.transfer_cost = pyo.Param(
        model.arcs,
        initialize=cost_data,
        within=pyo.Reals,
    )
    model.transfer = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def balance_rule(instance, hospital):
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
            instance.supply[hospital] + incoming - outgoing
            >= instance.demand[hospital]
        )

    model.hospital_balance = pyo.Constraint(
        model.hospitals, rule=balance_rule
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.transfer_cost[origin, destination]
            * model.transfer[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        # Leave unexpected runtime errors visible to the caller.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}