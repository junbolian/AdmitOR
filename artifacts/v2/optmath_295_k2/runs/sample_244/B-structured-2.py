# IR: {"sets":{"F":["facility_0","facility_1","facility_2","facility_3"],"C":["customer_0","customer_1","customer_2","customer_3","customer_4","customer_5"]},"params":{"fixed_cost":"F -> nonnegative real, from params","capacity":"F -> nonnegative real, from params","demand":"C -> nonnegative real, from params","shipping_cost":"F x C -> nonnegative real, from params"},"variables":{"opened[f]":"binary for f in F","shipment[f,c]":"nonnegative real for (f,c) in F x C"},"constraints":["sum(shipment[f,c] for f in F) == demand[c] for c in C","sum(shipment[f,c] for c in C) <= capacity[f]*opened[f] for f in F"],"objective":"minimize sum(fixed_cost[f]*opened[f] for f in F) + sum(shipping_cost[f,c]*shipment[f,c] for f in F,c in C)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _entry(values, position, label):
    """Accept sequences or mappings keyed by labels or integer positions."""
    if isinstance(values, Mapping):
        if label in values:
            return values[label]
        return values[position]
    return values[position]


def solve(params):
    facilities = tuple(f"facility_{idx}" for idx in range(4))
    customers = tuple(f"customer_{idx}" for idx in range(6))

    fixed_cost_data = params["fixed_cost"]
    capacity_data = params["capacity"]
    demand_data = params["demand"]
    shipping_cost_data = params["shipping_cost"]

    fixed_cost = {
        facility: _entry(fixed_cost_data, idx, facility)
        for idx, facility in enumerate(facilities)
    }
    capacity = {
        facility: _entry(capacity_data, idx, facility)
        for idx, facility in enumerate(facilities)
    }
    demand = {
        customer: _entry(demand_data, idx, customer)
        for idx, customer in enumerate(customers)
    }
    shipping_cost = {}
    for facility_idx, facility in enumerate(facilities):
        row = _entry(shipping_cost_data, facility_idx, facility)
        for customer_idx, customer in enumerate(customers):
            shipping_cost[facility, customer] = _entry(
                row, customer_idx, customer
            )

    model = pyo.ConcreteModel()
    model.F = pyo.Set(initialize=facilities, ordered=True)
    model.C = pyo.Set(initialize=customers, ordered=True)

    model.fixed_cost = pyo.Param(
        model.F, initialize=fixed_cost, within=pyo.NonNegativeReals
    )
    model.capacity = pyo.Param(
        model.F, initialize=capacity, within=pyo.NonNegativeReals
    )
    model.demand = pyo.Param(
        model.C, initialize=demand, within=pyo.NonNegativeReals
    )
    model.shipping_cost = pyo.Param(
        model.F,
        model.C,
        initialize=shipping_cost,
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.F, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.F, model.C, domain=pyo.NonNegativeReals
    )

    def demand_rule(instance, customer):
        return (
            sum(instance.shipment[facility, customer] for facility in instance.F)
            == instance.demand[customer]
        )

    model.demand_balance = pyo.Constraint(model.C, rule=demand_rule)

    def capacity_rule(instance, facility):
        return (
            sum(instance.shipment[facility, customer] for customer in instance.C)
            <= instance.capacity[facility] * instance.opened[facility]
        )

    model.capacity_link = pyo.Constraint(model.F, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[facility] * model.opened[facility]
            for facility in model.F
        )
        + sum(
            model.shipping_cost[facility, customer]
            * model.shipment[facility, customer]
            for facility in model.F
            for customer in model.C
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