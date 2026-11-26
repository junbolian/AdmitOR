# IR: {"sets":{"C":[1,2,3,4],"A":"{(i,j) in C x C: i != j}"},"params":{"stock":"stock[i] for i in C","demand":"demand[i] for i in C","cost":"cost_12,cost_13,cost_14,cost_21,cost_23,cost_24,cost_31,cost_32,cost_34,cost_41,cost_42,cost_43"},"variables":{"shipment[i,j]":"NonNegativeReals for (i,j) in A"},"constraints":["stock[i] + sum(shipment[j,i] for j != i) - sum(shipment[i,j] for j != i) >= demand[i] for i in C"],"objective":"minimize sum(cost[i,j] * shipment[i,j] for (i,j) in A)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Stock and demand accept four-element sequences or clinic-keyed mappings."""

    clinics = (1, 2, 3, 4)
    arcs = tuple(
        (origin, destination)
        for origin in clinics
        for destination in clinics
        if origin != destination
    )

    stock_data = params["stock"]
    demand_data = params["demand"]

    def clinic_value(data, clinic):
        if isinstance(data, Mapping):
            if clinic in data:
                return data[clinic]
            return data[str(clinic)]
        return data[clinic - 1]

    stock_values = {
        clinic: clinic_value(stock_data, clinic) for clinic in clinics
    }
    demand_values = {
        clinic: clinic_value(demand_data, clinic) for clinic in clinics
    }
    cost_values = {
        (1, 2): params["cost_12"],
        (1, 3): params["cost_13"],
        (1, 4): params["cost_14"],
        (2, 1): params["cost_21"],
        (2, 3): params["cost_23"],
        (2, 4): params["cost_24"],
        (3, 1): params["cost_31"],
        (3, 2): params["cost_32"],
        (3, 4): params["cost_34"],
        (4, 1): params["cost_41"],
        (4, 2): params["cost_42"],
        (4, 3): params["cost_43"],
    }

    model = pyo.ConcreteModel()
    model.clinics = pyo.Set(initialize=clinics, ordered=True)
    model.routes = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.initial_stock = pyo.Param(
        model.clinics, initialize=stock_values
    )
    model.required_supply = pyo.Param(
        model.clinics, initialize=demand_values
    )
    model.route_cost = pyo.Param(
        model.routes, initialize=cost_values
    )

    model.shipment = pyo.Var(
        model.routes, domain=pyo.NonNegativeReals
    )

    def supply_requirement_rule(instance, clinic):
        incoming = sum(
            instance.shipment[other, clinic]
            for other in instance.clinics
            if other != clinic
        )
        outgoing = sum(
            instance.shipment[clinic, other]
            for other in instance.clinics
            if other != clinic
        )
        return (
            instance.initial_stock[clinic] + incoming - outgoing
            >= instance.required_supply[clinic]
        )

    model.supply_requirement = pyo.Constraint(
        model.clinics, rule=supply_requirement_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.route_cost[origin, destination]
            * model.shipment[origin, destination]
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