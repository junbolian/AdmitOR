# IR: {"sets":{"devices":["A","B","C","D"]},"params":{"demand":"required total production","prep_cost":"device-keyed mapping or sequence ordered A,B,C,D","unit_cost":"device-keyed mapping or sequence ordered A,B,C,D","capacity":"device-keyed mapping or sequence ordered A,B,C,D"},"variables":{"production[d]":"NonNegativeReals","enabled[d]":"Binary"},"constraints":["sum(production[d] for d in devices) == demand","production[d] <= capacity[d] * enabled[d] for each d in devices"],"objective":"minimize sum(prep_cost[d] * enabled[d] + unit_cost[d] * production[d] for d in devices)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept device data as mappings or sequences in A, B, C, D order."""
    devices = ("A", "B", "C", "D")

    def device_values(values):
        if isinstance(values, Mapping):
            return {device: values[device] for device in devices}
        if len(values) != len(devices):
            raise ValueError("Device parameter sequences must contain four values.")
        return {
            device: values[position]
            for position, device in enumerate(devices)
        }

    demand = params["demand"]
    prep_cost = device_values(params["prep_cost"])
    unit_cost = device_values(params["unit_cost"])
    capacity = device_values(params["capacity"])

    model = pyo.ConcreteModel()
    model.devices = pyo.Set(initialize=devices, ordered=True)

    model.required_production = pyo.Param(initialize=demand)
    model.fixed_cost = pyo.Param(model.devices, initialize=prep_cost)
    model.variable_cost = pyo.Param(model.devices, initialize=unit_cost)
    model.device_capacity = pyo.Param(model.devices, initialize=capacity)

    model.production = pyo.Var(model.devices, domain=pyo.NonNegativeReals)
    model.enabled = pyo.Var(model.devices, domain=pyo.Binary)

    model.production_requirement = pyo.Constraint(
        expr=sum(model.production[device] for device in model.devices)
        == model.required_production
    )

    def capacity_rule(instance, device):
        return (
            instance.production[device]
            <= instance.device_capacity[device] * instance.enabled[device]
        )

    model.capacity_limits = pyo.Constraint(
        model.devices, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[device] * model.enabled[device]
            + model.variable_cost[device] * model.production[device]
            for device in model.devices
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # An infeasible solve may raise when no solution can be loaded.
        # Determine success exclusively through objective retrieval below.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}