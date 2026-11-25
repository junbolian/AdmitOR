# IR: {"sets":{"F":"facility_0..facility_5","C":"customer_0..customer_10","A":"facility-customer pairs with shipping costs supplied in params"},"params":{"fixed_cost_facility":"opening costs on F","capacity_facility":"capacities on F","demand_customer":"demands on C","shipping_cost_per_unit":"observed shipping costs on A; a single flat row refers to facility_0; unobserved coefficients are omitted"},"variables":{"opened[f]":"binary","shipped[f,c]":"nonnegative continuous"},"constraints":["For each c: sum_f shipped[f,c] = demand_customer[c]","For each f: sum_c shipped[f,c] <= capacity_facility[f]*opened[f]"],"objective":"minimize sum_f fixed_cost_facility[f]*opened[f] + sum_(f,c) in A shipping_cost_per_unit[f,c]*shipped[f,c]"}
from collections.abc import Mapping, Sequence

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


_MISSING = object()


def _is_sequence(value):
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes))


def _lookup(data, keys):
    for key in keys:
        if key in data:
            return data[key]
    return _MISSING


def _indexed_value(data, label, position):
    if isinstance(data, Mapping):
        value = _lookup(data, (label, label.capitalize(), position, str(position)))
        if value is _MISSING:
            raise KeyError(label)
        return value
    return data[position]


def _shipping_coefficients(data, facilities, customers):
    """Read complete matrices or partially observed shipping coefficients."""
    coefficients = {}
    customer_count = len(customers)
    facility_count = len(facilities)

    if _is_sequence(data):
        # A flat vector is either the observed facility_0 row or a full,
        # row-major flattened matrix.
        if all(not isinstance(value, Mapping) and not _is_sequence(value)
               for value in data):
            if len(data) not in (customer_count, facility_count * customer_count):
                raise ValueError("Unexpected flat shipping-cost vector length")
            for position, value in enumerate(data):
                facility_pos, customer_pos = divmod(position, customer_count)
                coefficients[
                    facilities[facility_pos], customers[customer_pos]
                ] = value
            return coefficients

        if len(data) > facility_count:
            raise ValueError("Too many shipping-cost rows")
        for facility_pos, row in enumerate(data):
            if row is None:
                continue
            for customer_pos, customer in enumerate(customers):
                if isinstance(row, Mapping):
                    value = _lookup(
                        row,
                        (customer, customer.capitalize(),
                         customer_pos, str(customer_pos)),
                    )
                elif _is_sequence(row):
                    value = (
                        row[customer_pos]
                        if customer_pos < len(row)
                        else _MISSING
                    )
                else:
                    raise TypeError("Shipping-cost rows must be indexed data")
                if value is not _MISSING and value is not None:
                    coefficients[facilities[facility_pos], customer] = value
        return coefficients

    if not isinstance(data, Mapping):
        raise TypeError("Shipping costs must be a mapping or sequence")

    # Numeric flat dictionaries can represent one row or a row-major matrix.
    numeric_keys = []
    for key in data:
        if isinstance(key, int):
            numeric_keys.append(key)
        elif isinstance(key, str) and key.isdigit():
            numeric_keys.append(int(key))

    flat_numeric = (
        len(numeric_keys) == len(data)
        and all(not isinstance(value, Mapping) and not _is_sequence(value)
                for value in data.values())
    )
    if flat_numeric:
        for position in numeric_keys:
            if not 0 <= position < facility_count * customer_count:
                raise ValueError("Shipping-cost index out of range")
            facility_pos, customer_pos = divmod(position, customer_count)
            value = _lookup(data, (position, str(position)))
            if value is not None:
                coefficients[
                    facilities[facility_pos], customers[customer_pos]
                ] = value
        return coefficients

    for facility_pos, facility in enumerate(facilities):
        row = _lookup(
            data,
            (facility, facility.capitalize(), facility_pos, str(facility_pos)),
        )
        for customer_pos, customer in enumerate(customers):
            value = _lookup(
                data,
                (
                    (facility, customer),
                    (facility.capitalize(), customer.capitalize()),
                    (facility_pos, customer_pos),
                    (str(facility_pos), str(customer_pos)),
                    f"{facility}_{customer}",
                    f"{facility.capitalize()}_{customer.capitalize()}",
                    f"{facility},{customer}",
                    f"{facility}->{customer}",
                ),
            )

            if value is _MISSING and row is not _MISSING and row is not None:
                if isinstance(row, Mapping):
                    value = _lookup(
                        row,
                        (customer, customer.capitalize(),
                         customer_pos, str(customer_pos)),
                    )
                elif _is_sequence(row):
                    if customer_pos < len(row):
                        value = row[customer_pos]
                else:
                    raise TypeError("Shipping-cost rows must be indexed data")

            # A customer-indexed dictionary is the observed facility_0 row.
            if value is _MISSING and facility_pos == 0:
                value = _lookup(data, (customer, customer.capitalize()))

            if value is not _MISSING and value is not None:
                coefficients[facility, customer] = value

    if data and not coefficients:
        raise ValueError("Unrecognized shipping-cost indexing")
    return coefficients


def solve(params):
    fixed_data = params["fixed_cost_facility"]
    capacity_data = params["capacity_facility"]
    demand_data = params["demand_customer"]
    shipping_data = params["shipping_cost_per_unit"]

    facilities = [f"facility_{idx}" for idx in range(6)]
    customers = [f"customer_{idx}" for idx in range(11)]

    fixed_cost = {
        facility: _indexed_value(fixed_data, facility, position)
        for position, facility in enumerate(facilities)
    }
    capacity = {
        facility: _indexed_value(capacity_data, facility, position)
        for position, facility in enumerate(facilities)
    }
    demand = {
        customer: _indexed_value(demand_data, customer, position)
        for position, customer in enumerate(customers)
    }
    shipping_cost = _shipping_coefficients(
        shipping_data, facilities, customers
    )

    model = pyo.ConcreteModel()
    model.F = pyo.Set(initialize=facilities, ordered=True)
    model.C = pyo.Set(initialize=customers, ordered=True)
    model.A = pyo.Set(
        dimen=2, initialize=list(shipping_cost), ordered=True
    )

    model.fixed_cost = pyo.Param(model.F, initialize=fixed_cost)
    model.capacity = pyo.Param(model.F, initialize=capacity)
    model.demand = pyo.Param(model.C, initialize=demand)
    model.shipping_cost = pyo.Param(model.A, initialize=shipping_cost)

    model.opened = pyo.Var(model.F, domain=pyo.Binary)
    model.shipped = pyo.Var(model.F, model.C, domain=pyo.NonNegativeReals)

    def demand_rule(instance, customer):
        return sum(
            instance.shipped[facility, customer]
            for facility in instance.F
        ) == instance.demand[customer]

    def capacity_rule(instance, facility):
        return sum(
            instance.shipped[facility, customer]
            for customer in instance.C
        ) <= instance.capacity[facility] * instance.opened[facility]

    model.demand_satisfaction = pyo.Constraint(model.C, rule=demand_rule)
    model.capacity_activation = pyo.Constraint(model.F, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[facility] * model.opened[facility]
            for facility in model.F
        ) + sum(
            model.shipping_cost[facility, customer]
            * model.shipped[facility, customer]
            for facility, customer in model.A
        ),
        sense=pyo.minimize,
    )

    # Appsi may raise when it cannot load a feasible solution. Only objective
    # retrieval below determines whether this call reports success.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}