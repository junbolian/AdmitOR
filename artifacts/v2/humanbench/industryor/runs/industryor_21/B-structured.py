# IR: {"sets":{"I":"{1,...,6}","A":"{(i,j) in I x I: capacity[i] >= capacity[j]}"},"params":{"capacity":"params['capacity'], indexed by I","demand":"params['demand'], indexed by I, nonnegative integers","variable_cost":"params['variable_cost'], indexed by I","fixed_cost":"params['fixed_cost'], scalar","U[i]":"sum(demand[j] for j in I if (i,j) in A)"},"variables":{"x[i,j]":"nonnegative integer for (i,j) in A; type i units assigned to demand j","y[i]":"binary; whether type i is produced"},"constraints":["For each j in I: sum(x[i,j] for i with (i,j) in A) = demand[j]","For each i in I: sum(x[i,j] for j with (i,j) in A) <= U[i]*y[i]"],"objective":"minimize sum(variable_cost[i]*x[i,j] for (i,j) in A) + fixed_cost*sum(y[i] for i in I)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _indexed_value(values, code):
    """Accept a six-element sequence or a mapping keyed by 1..6 or '1'..'6'."""
    if isinstance(values, Mapping):
        if code in values:
            return values[code]
        return values[str(code)]
    return values[code - 1]


def solve(params):
    type_codes = tuple(range(1, 7))

    capacity_input = params["capacity"]
    demand_input = params["demand"]
    variable_cost_input = params["variable_cost"]
    fixed_cost_input = params["fixed_cost"]

    capacities = {
        code: _indexed_value(capacity_input, code) for code in type_codes
    }
    demands = {
        code: _indexed_value(demand_input, code) for code in type_codes
    }
    variable_costs = {
        code: _indexed_value(variable_cost_input, code) for code in type_codes
    }

    allowed_pairs = [
        (producer, customer)
        for producer in type_codes
        for customer in type_codes
        if capacities[producer] >= capacities[customer]
    ]

    customers_by_producer = {
        producer: [
            customer
            for customer in type_codes
            if (producer, customer) in allowed_pairs
        ]
        for producer in type_codes
    }
    producers_by_customer = {
        customer: [
            producer
            for producer in type_codes
            if (producer, customer) in allowed_pairs
        ]
        for customer in type_codes
    }

    model = pyo.ConcreteModel()
    model.type_codes = pyo.Set(initialize=type_codes, ordered=True)
    model.allowed_pairs = pyo.Set(dimen=2, initialize=allowed_pairs)

    model.capacity = pyo.Param(
        model.type_codes, initialize=capacities, within=pyo.NonNegativeReals
    )
    model.demand = pyo.Param(
        model.type_codes, initialize=demands, within=pyo.NonNegativeIntegers
    )
    model.variable_cost = pyo.Param(
        model.type_codes, initialize=variable_costs, within=pyo.NonNegativeReals
    )
    model.fixed_cost = pyo.Param(
        initialize=fixed_cost_input, within=pyo.NonNegativeReals
    )
    model.output_limit = pyo.Param(
        model.type_codes,
        initialize={
            producer: sum(
                demands[customer]
                for customer in customers_by_producer[producer]
            )
            for producer in type_codes
        },
        within=pyo.NonNegativeIntegers,
    )

    model.allocation = pyo.Var(
        model.allowed_pairs, domain=pyo.NonNegativeIntegers
    )
    model.produce_type = pyo.Var(model.type_codes, domain=pyo.Binary)

    def demand_rule(instance, customer):
        return sum(
            instance.allocation[producer, customer]
            for producer in producers_by_customer[customer]
        ) == instance.demand[customer]

    model.demand_fulfillment = pyo.Constraint(
        model.type_codes, rule=demand_rule
    )

    def activation_rule(instance, producer):
        return sum(
            instance.allocation[producer, customer]
            for customer in customers_by_producer[producer]
        ) <= instance.output_limit[producer] * instance.produce_type[producer]

    model.production_activation = pyo.Constraint(
        model.type_codes, rule=activation_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.variable_cost[producer]
            * model.allocation[producer, customer]
            for producer, customer in model.allowed_pairs
        )
        + model.fixed_cost
        * sum(model.produce_type[producer] for producer in model.type_codes),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}