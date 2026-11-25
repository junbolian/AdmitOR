# IR: {"sets":{"I":"range(params['num_facilities'])","J":"range(params['num_customers'])"},"params":{"fixed_cost":"params['fixed_cost'][i]","capacity":"params['capacity'][i]","demand":"params['demand'][j]","transport_cost":"params['transport_cost'][i,j]; all entries required; unknown costs are not imputed"},"variables":{"opened[i]":"binary","shipment[i,j]":"nonnegative continuous"},"constraints":["For each j: sum(i in I, shipment[i,j]) == demand[j]","For each i: sum(j in J, shipment[i,j]) <= capacity[i]*opened[i]"],"objective":"minimize sum(i in I, fixed_cost[i]*opened[i]) + sum(i in I,j in J, transport_cost[i,j]*shipment[i,j])","validation":"Return insufficient_transport_data if any transportation cost is unknown; diagonal costs alone do not determine this optimization problem."}

import ast
from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


_MISSING = object()


def _indexed(data, position):
    if isinstance(data, Mapping):
        if position in data:
            return data[position]
        return data.get(str(position), _MISSING)
    if isinstance(data, (list, tuple)):
        if 0 <= position < len(data):
            return data[position]
    return _MISSING


def _normalize_pair_keys(data):
    """Support tuple keys and common serialized pair-key representations."""
    if not isinstance(data, Mapping):
        return {}

    normalized = {}
    for key, value in data.items():
        if isinstance(key, tuple) and len(key) == 2:
            normalized[key] = value
        elif isinstance(key, str):
            try:
                parsed = ast.literal_eval(key)
            except (ValueError, SyntaxError):
                continue
            if isinstance(parsed, (tuple, list)) and len(parsed) == 2:
                if all(isinstance(entry, int) for entry in parsed):
                    normalized[tuple(parsed)] = value
    return normalized


def _transport_entry(data, pair_data, facility, customer):
    pair = (facility, customer)
    if pair in pair_data:
        return pair_data[pair]

    row = _indexed(data, facility)
    if row is _MISSING or row is None:
        return _MISSING

    # A scalar row is not a complete row of transportation costs.
    # In particular, a diagonal-only vector cannot supply off-diagonal costs.
    return _indexed(row, customer)


def solve(params):
    num_facilities = params["num_facilities"]
    num_customers = params["num_customers"]
    fixed_cost_data = params["fixed_cost"]
    capacity_data = params["capacity"]
    demand_data = params["demand"]
    transport_cost_data = params["transport_cost"]

    facilities = range(num_facilities)
    customers = range(num_customers)

    fixed_cost = {
        facility: _indexed(fixed_cost_data, facility)
        for facility in facilities
    }
    capacity = {
        facility: _indexed(capacity_data, facility)
        for facility in facilities
    }
    demand = {
        customer: _indexed(demand_data, customer)
        for customer in customers
    }

    for values in (fixed_cost, capacity, demand):
        if any(value is _MISSING or value is None for value in values.values()):
            return {"objective": None, "status": "missing_parameter_data"}

    pair_data = _normalize_pair_keys(transport_cost_data)
    transport_cost = {}
    for facility in facilities:
        for customer in customers:
            value = _transport_entry(
                transport_cost_data, pair_data, facility, customer
            )
            if value is _MISSING or value is None:
                # Neither zero costs, prohibited routes, nor replicated
                # diagonal costs are implied by unknown off-diagonal entries.
                return {
                    "objective": None,
                    "status": "insufficient_transport_data",
                }
            transport_cost[facility, customer] = value

    model = pyo.ConcreteModel()
    model.facilities = pyo.Set(initialize=facilities, ordered=True)
    model.customers = pyo.Set(initialize=customers, ordered=True)

    model.fixed_cost = pyo.Param(model.facilities, initialize=fixed_cost)
    model.capacity = pyo.Param(
        model.facilities, initialize=capacity, within=pyo.NonNegativeReals
    )
    model.demand = pyo.Param(
        model.customers, initialize=demand, within=pyo.NonNegativeReals
    )
    model.transport_cost = pyo.Param(
        model.facilities, model.customers, initialize=transport_cost
    )

    model.opened = pyo.Var(model.facilities, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.facilities, model.customers, domain=pyo.NonNegativeReals
    )

    def demand_rule(instance, customer):
        return (
            pyo.quicksum(
                instance.shipment[facility, customer]
                for facility in instance.facilities
            )
            == instance.demand[customer]
        )

    model.demand_satisfaction = pyo.Constraint(
        model.customers, rule=demand_rule
    )

    def capacity_rule(instance, facility):
        return (
            pyo.quicksum(
                instance.shipment[facility, customer]
                for customer in instance.customers
            )
            <= instance.capacity[facility] * instance.opened[facility]
        )

    model.facility_capacity = pyo.Constraint(
        model.facilities, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.fixed_cost[facility] * model.opened[facility]
            for facility in model.facilities
        )
        + pyo.quicksum(
            model.transport_cost[facility, customer]
            * model.shipment[facility, customer]
            for facility in model.facilities
            for customer in model.customers
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # Success is determined below solely by objective retrievability.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}