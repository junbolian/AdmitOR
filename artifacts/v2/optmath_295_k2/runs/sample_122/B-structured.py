# IR: {"sets":{"P":"0..5","C":"0..5"},"params":{"production_cost":"real[P,C]","producer_capacity":"nonnegative real[P]","contract_demand":"nonnegative real[C]","min_contributors":"nonnegative integer[C]","min_delivery_per_producer":"nonnegative real[P]"},"variables":{"delivery[P,C]":"nonnegative continuous","contributes[P,C]":"binary"},"constraints":["For each p: sum_c delivery[p,c] <= producer_capacity[p]","For each c: sum_p delivery[p,c] >= contract_demand[c]","For each c: sum_p contributes[p,c] >= min_contributors[c]","For each p,c: delivery[p,c] >= min_delivery_per_producer[p] * contributes[p,c]","For each p,c: delivery[p,c] <= producer_capacity[p] * contributes[p,c]"],"objective":"Minimize sum_p,c production_cost[p,c] * delivery[p,c]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.producers = pyo.RangeSet(0, 5)
    model.contracts = pyo.RangeSet(0, 5)

    model.production_cost = pyo.Param(
        model.producers,
        model.contracts,
        initialize={
            (producer, contract): params["production_cost"][producer][contract]
            for producer in model.producers
            for contract in model.contracts
        },
        within=pyo.Reals,
    )
    model.producer_capacity = pyo.Param(
        model.producers,
        initialize={
            producer: params["producer_capacity"][producer]
            for producer in model.producers
        },
        within=pyo.NonNegativeReals,
    )
    model.contract_demand = pyo.Param(
        model.contracts,
        initialize={
            contract: params["contract_demand"][contract]
            for contract in model.contracts
        },
        within=pyo.NonNegativeReals,
    )
    model.min_contributors = pyo.Param(
        model.contracts,
        initialize={
            contract: params["min_contributors"][contract]
            for contract in model.contracts
        },
        within=pyo.NonNegativeIntegers,
    )
    model.min_delivery_per_producer = pyo.Param(
        model.producers,
        initialize={
            producer: params["min_delivery_per_producer"][producer]
            for producer in model.producers
        },
        within=pyo.NonNegativeReals,
    )

    model.delivery = pyo.Var(
        model.producers,
        model.contracts,
        domain=pyo.NonNegativeReals,
    )
    model.contributes = pyo.Var(
        model.producers,
        model.contracts,
        domain=pyo.Binary,
    )

    def capacity_rule(instance, producer):
        return (
            sum(
                instance.delivery[producer, contract]
                for contract in instance.contracts
            )
            <= instance.producer_capacity[producer]
        )

    model.capacity_limits = pyo.Constraint(
        model.producers, rule=capacity_rule
    )

    def demand_rule(instance, contract):
        return (
            sum(
                instance.delivery[producer, contract]
                for producer in instance.producers
            )
            >= instance.contract_demand[contract]
        )

    model.contract_fulfillment = pyo.Constraint(
        model.contracts, rule=demand_rule
    )

    def contributors_rule(instance, contract):
        return (
            sum(
                instance.contributes[producer, contract]
                for producer in instance.producers
            )
            >= instance.min_contributors[contract]
        )

    model.contributor_requirements = pyo.Constraint(
        model.contracts, rule=contributors_rule
    )

    def minimum_delivery_rule(instance, producer, contract):
        return (
            instance.delivery[producer, contract]
            >= instance.min_delivery_per_producer[producer]
            * instance.contributes[producer, contract]
        )

    model.minimum_delivery_links = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=minimum_delivery_rule,
    )

    def maximum_delivery_rule(instance, producer, contract):
        return (
            instance.delivery[producer, contract]
            <= instance.producer_capacity[producer]
            * instance.contributes[producer, contract]
        )

    model.maximum_delivery_links = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=maximum_delivery_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.production_cost[producer, contract]
            * model.delivery[producer, contract]
            for producer in model.producers
            for contract in model.contracts
        ),
        sense=pyo.minimize,
    )

    # HiGHS raises RuntimeError when it cannot load a feasible solution.
    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    # Success is determined solely by retrieving the objective value.
    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}