# IR: {
#   "sets": {"devices": ["A", "B", "C", "D"]},
#   "params": {"setup_cost": "nonnegative real[devices]", "production_cost": "nonnegative real[devices]", "capacity": "nonnegative real[devices]", "demand": "nonnegative real"},
#   "variables": {"production[d]": "nonnegative integer", "activated[d]": "binary"},
#   "constraints": [
#     "sum(production[d] for d in devices) == demand",
#     "production[d] <= capacity[d] * activated[d] for each d in devices"
#   ],
#   "objective": "minimize sum(setup_cost[d] * activated[d] + production_cost[d] * production[d] for d in devices)"
# }

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Device parameters accept mappings keyed A-D or sequences ordered A-D."""
    devices = ("A", "B", "C", "D")

    def device_values(values):
        if isinstance(values, Mapping):
            return {device: values[device] for device in devices}
        return {
            device: values[position]
            for position, device in enumerate(devices)
        }

    setup_cost = device_values(params["setup_cost"])
    production_cost = device_values(params["production_cost"])
    capacity = device_values(params["capacity"])
    demand = params["demand"]

    model = pyo.ConcreteModel()
    model.devices = pyo.Set(initialize=devices, ordered=True)

    model.setup_cost = pyo.Param(
        model.devices, initialize=setup_cost, within=pyo.NonNegativeReals
    )
    model.production_cost = pyo.Param(
        model.devices, initialize=production_cost, within=pyo.NonNegativeReals
    )
    model.capacity = pyo.Param(
        model.devices, initialize=capacity, within=pyo.NonNegativeReals
    )
    model.demand = pyo.Param(
        initialize=demand, within=pyo.NonNegativeReals
    )

    model.production = pyo.Var(
        model.devices, domain=pyo.NonNegativeIntegers
    )
    model.activated = pyo.Var(model.devices, domain=pyo.Binary)

    model.demand_balance = pyo.Constraint(
        expr=sum(model.production[device] for device in model.devices)
        == model.demand
    )

    def capacity_rule(instance, device):
        return (
            instance.production[device]
            <= instance.capacity[device] * instance.activated[device]
        )

    model.capacity_limit = pyo.Constraint(
        model.devices, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.setup_cost[device] * model.activated[device]
            + model.production_cost[device] * model.production[device]
            for device in model.devices
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