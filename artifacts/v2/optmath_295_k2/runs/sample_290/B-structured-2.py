# IR: {"sets":{"I":"range(params['num_facilities'])","J":"range(params['num_customers'])"},"params":{"fixed_cost":"params['fixed_cost'][i]","capacity":"params['capacity'][i]","demand":"params['demand'][j]","transport_cost":"Explicit params['transport_cost'][i,j] or nested [i][j] when available; otherwise use the supplied facility-i scalar/diagonal rate for every customer (explicit modeling assumption for unspecified off-diagonal costs)."},"variables":{"open_facility[i]":"Binary","ship[i,j]":"NonNegativeReals"},"constraints":["sum(ship[i,j] for i in I) == demand[j] for each j in J","sum(ship[i,j] for j in J) <= capacity[i]*open_facility[i] for each i in I"],"objective":"minimize sum(fixed_cost[i]*open_facility[i] for i in I) + sum(transport_cost[i,j]*ship[i,j] for i in I for j in J)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _indexed_value(data, index):
    if isinstance(data, Mapping):
        if index in data:
            return data[index]
        return data[str(index)]
    return data[index]


def _is_indexed(value):
    return isinstance(value, Mapping) or (
        hasattr(value, "__getitem__")
        and not isinstance(value, (str, bytes))
    )


def _explicit_pair(data, facility, customer):
    if isinstance(data, Mapping):
        for key in (
            (facility, customer),
            f"{facility},{customer}",
            f"({facility}, {customer})",
        ):
            if key in data:
                value = data[key]
                if value is not None:
                    return value

    try:
        row = _indexed_value(data, facility)
    except (KeyError, IndexError):
        raise KeyError((facility, customer)) from None

    if _is_indexed(row):
        value = _indexed_value(row, customer)
        if value is not None:
            return value

    raise KeyError((facility, customer))


def _transport_value(data, facility, customer):
    try:
        return _explicit_pair(data, facility, customer)
    except (KeyError, IndexError):
        pass

    # Explicit assumption: a supplied scalar or diagonal cost for a facility
    # is its per-unit shipping rate to customers with unspecified costs.
    try:
        row = _indexed_value(data, facility)
    except (KeyError, IndexError):
        row = None

    if row is not None and not _is_indexed(row):
        return row

    return _explicit_pair(data, facility, facility)


def solve(params):
    num_facilities = params["num_facilities"]
    num_customers = params["num_customers"]
    fixed_cost_input = params["fixed_cost"]
    capacity_input = params["capacity"]
    demand_input = params["demand"]
    transport_cost_input = params["transport_cost"]

    facilities = range(num_facilities)
    customers = range(num_customers)

    fixed_cost = {
        facility: _indexed_value(fixed_cost_input, facility)
        for facility in facilities
    }
    capacity = {
        facility: _indexed_value(capacity_input, facility)
        for facility in facilities
    }
    demand = {
        customer: _indexed_value(demand_input, customer)
        for customer in customers
    }

    transport_cost = {}
    for facility in facilities:
        for customer in customers:
            try:
                transport_cost[facility, customer] = _transport_value(
                    transport_cost_input, facility, customer
                )
            except (KeyError, IndexError):
                return {"objective": None, "status": "missing_transport_cost"}

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
        model.facilities,
        model.customers,
        initialize=transport_cost,
        within=pyo.Reals,
    )

    model.open_facility = pyo.Var(model.facilities, domain=pyo.Binary)
    model.ship = pyo.Var(
        model.facilities, model.customers, domain=pyo.NonNegativeReals
    )

    def demand_rule(instance, customer):
        return (
            sum(
                instance.ship[facility, customer]
                for facility in instance.facilities
            )
            == instance.demand[customer]
        )

    def capacity_rule(instance, facility):
        return (
            sum(
                instance.ship[facility, customer]
                for customer in instance.customers
            )
            <= instance.capacity[facility] * instance.open_facility[facility]
        )

    model.demand_satisfaction = pyo.Constraint(
        model.customers, rule=demand_rule
    )
    model.facility_capacity = pyo.Constraint(
        model.facilities, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[facility] * model.open_facility[facility]
            for facility in model.facilities
        )
        + sum(
            model.transport_cost[facility, customer]
            * model.ship[facility, customer]
            for facility in model.facilities
            for customer in model.customers
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