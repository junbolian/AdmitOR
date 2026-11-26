# IR: {"sets":{"clinics":[1,2,3,4],"arcs":"all ordered pairs (i,j) of distinct clinics"},"params":{"initial_stock":"indexed by clinic","required_demand":"indexed by clinic","transport_cost_1_to_2":"unit cost","transport_cost_1_to_3":"unit cost","transport_cost_1_to_4":"unit cost","transport_cost_2_to_1":"unit cost","transport_cost_2_to_3":"unit cost","transport_cost_2_to_4":"unit cost","transport_cost_3_to_1":"unit cost","transport_cost_3_to_2":"unit cost","transport_cost_3_to_4":"unit cost","transport_cost_4_to_1":"unit cost","transport_cost_4_to_2":"unit cost","transport_cost_4_to_3":"unit cost"},"variables":{"shipment[i,j]":"nonnegative continuous, (i,j) in arcs"},"constraints":["initial_stock[i] + sum(shipment[j,i] for j != i) - sum(shipment[i,j] for j != i) >= required_demand[i], for each clinic i"],"objective":"minimize sum(transport_cost[i,j] * shipment[i,j] for (i,j) in arcs)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _clinic_values(values):
    """Accept clinic-keyed mappings or sequences ordered Clinics 1 through 4."""
    if isinstance(values, Mapping):
        return {
            clinic: values[clinic] if clinic in values else values[str(clinic)]
            for clinic in range(1, 5)
        }
    return {clinic: values[clinic - 1] for clinic in range(1, 5)}


def solve(params):
    initial_stock = _clinic_values(params["initial_stock"])
    required_demand = _clinic_values(params["required_demand"])

    transport_cost = {
        (1, 2): params["transport_cost_1_to_2"],
        (1, 3): params["transport_cost_1_to_3"],
        (1, 4): params["transport_cost_1_to_4"],
        (2, 1): params["transport_cost_2_to_1"],
        (2, 3): params["transport_cost_2_to_3"],
        (2, 4): params["transport_cost_2_to_4"],
        (3, 1): params["transport_cost_3_to_1"],
        (3, 2): params["transport_cost_3_to_2"],
        (3, 4): params["transport_cost_3_to_4"],
        (4, 1): params["transport_cost_4_to_1"],
        (4, 2): params["transport_cost_4_to_2"],
        (4, 3): params["transport_cost_4_to_3"],
    }

    model = pyo.ConcreteModel()

    model.clinics = pyo.Set(initialize=range(1, 5), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in range(1, 5)
            for destination in range(1, 5)
            if origin != destination
        ],
        ordered=True,
    )

    model.initial_stock = pyo.Param(
        model.clinics, initialize=initial_stock
    )
    model.required_demand = pyo.Param(
        model.clinics, initialize=required_demand
    )
    model.transport_cost = pyo.Param(
        model.arcs, initialize=transport_cost
    )

    model.shipment = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

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
            >= instance.required_demand[clinic]
        )

    model.supply_requirement = pyo.Constraint(
        model.clinics, rule=supply_requirement_rule
    )

    model.total_transport_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[origin, destination]
            * model.shipment[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_transport_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}