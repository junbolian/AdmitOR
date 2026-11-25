# IR: {
#   "sets": {"P": [0,1,2,3,4,5], "C": [0,1,2,3,4,5]},
#   "params": {"producer_capacity": "nonnegative[P]", "contract_demand": "nonnegative[C]", "min_contributors": "nonnegative_integer[C]", "producer_min_delivery": "nonnegative[P]", "cost_coefficient": "real[P,C]; accepts nested data, producer-major flat data, producer-wise values, or a scalar"},
#   "variables": {"delivery": "nonnegative_continuous[P,C]", "contributes": "binary[P,C]"},
#   "constraints": [
#     "capacity[p]: sum(delivery[p,c] for c in C) <= producer_capacity[p]",
#     "fulfillment[c]: sum(delivery[p,c] for p in P) >= contract_demand[c]",
#     "contributors[c]: sum(contributes[p,c] for p in P) >= min_contributors[c]",
#     "minimum_delivery[p,c]: delivery[p,c] >= producer_min_delivery[p] * contributes[p,c]",
#     "activation[p,c]: delivery[p,c] <= producer_capacity[p] * contributes[p,c]"
#   ],
#   "objective": "minimize sum(cost_coefficient[p,c] * delivery[p,c] for p in P for c in C)"
# }

from collections.abc import Mapping
from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Build and solve the electricity delivery MILP.

    Vectors accept sequences or mappings keyed by integers or integer strings.

    cost_coefficient accepts:
      * A nested 6-by-6 sequence or mapping.
      * A mapping keyed by (producer, contract).
      * A flat sequence of 36 values in producer-major order.
      * A flat sequence of 6 producer-specific values, shared across contracts.
      * A scalar, shared across all producer-contract pairs.
    """
    producer_capacity = params["producer_capacity"]
    contract_demand = params["contract_demand"]
    min_contributors = params["min_contributors"]
    producer_min_delivery = params["producer_min_delivery"]
    cost_coefficient = params["cost_coefficient"]

    def indexed(data, position):
        if isinstance(data, Mapping):
            if position in data:
                return data[position]
            return data[str(position)]
        return data[position]

    def read_cost(producer, contract):
        if isinstance(cost_coefficient, Number):
            return cost_coefficient

        if isinstance(cost_coefficient, Mapping):
            pair = (producer, contract)
            if pair in cost_coefficient:
                return cost_coefficient[pair]

            row = indexed(cost_coefficient, producer)
            if isinstance(row, Number):
                return row
            return indexed(row, contract)

        count = len(cost_coefficient)

        if count == 36:
            return cost_coefficient[producer * 6 + contract]

        if count == 6:
            row = cost_coefficient[producer]
            if isinstance(row, Number):
                return row
            return indexed(row, contract)

        raise ValueError(
            "cost_coefficient must be a scalar, a 6-by-6 structure, "
            "a pair-keyed mapping, or a flat sequence of 6 or 36 values."
        )

    model = pyo.ConcreteModel()
    model.P = pyo.RangeSet(0, 5)
    model.C = pyo.RangeSet(0, 5)

    model.producer_capacity = pyo.Param(
        model.P,
        initialize={
            producer: indexed(producer_capacity, producer)
            for producer in model.P
        },
        within=pyo.NonNegativeReals,
    )
    model.contract_demand = pyo.Param(
        model.C,
        initialize={
            contract: indexed(contract_demand, contract)
            for contract in model.C
        },
        within=pyo.NonNegativeReals,
    )
    model.min_contributors = pyo.Param(
        model.C,
        initialize={
            contract: indexed(min_contributors, contract)
            for contract in model.C
        },
        within=pyo.NonNegativeIntegers,
    )
    model.producer_min_delivery = pyo.Param(
        model.P,
        initialize={
            producer: indexed(producer_min_delivery, producer)
            for producer in model.P
        },
        within=pyo.NonNegativeReals,
    )
    model.cost_coefficient = pyo.Param(
        model.P,
        model.C,
        initialize={
            (producer, contract): read_cost(producer, contract)
            for producer in model.P
            for contract in model.C
        },
        within=pyo.Reals,
    )

    model.delivery = pyo.Var(
        model.P, model.C, domain=pyo.NonNegativeReals
    )
    model.contributes = pyo.Var(
        model.P, model.C, domain=pyo.Binary
    )

    def capacity_rule(problem, producer):
        return (
            sum(
                problem.delivery[producer, contract]
                for contract in problem.C
            )
            <= problem.producer_capacity[producer]
        )

    model.capacity = pyo.Constraint(model.P, rule=capacity_rule)

    def fulfillment_rule(problem, contract):
        return (
            sum(
                problem.delivery[producer, contract]
                for producer in problem.P
            )
            >= problem.contract_demand[contract]
        )

    model.fulfillment = pyo.Constraint(model.C, rule=fulfillment_rule)

    def contributors_rule(problem, contract):
        return (
            sum(
                problem.contributes[producer, contract]
                for producer in problem.P
            )
            >= problem.min_contributors[contract]
        )

    model.contributors = pyo.Constraint(model.C, rule=contributors_rule)

    def minimum_delivery_rule(problem, producer, contract):
        return (
            problem.delivery[producer, contract]
            >= problem.producer_min_delivery[producer]
            * problem.contributes[producer, contract]
        )

    model.minimum_delivery = pyo.Constraint(
        model.P, model.C, rule=minimum_delivery_rule
    )

    def activation_rule(problem, producer, contract):
        return (
            problem.delivery[producer, contract]
            <= problem.producer_capacity[producer]
            * problem.contributes[producer, contract]
        )

    model.activation = pyo.Constraint(
        model.P, model.C, rule=activation_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost_coefficient[producer, contract]
            * model.delivery[producer, contract]
            for producer in model.P
            for contract in model.C
        ),
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