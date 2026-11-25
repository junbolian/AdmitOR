# IR: {"sets":{"P":[0,1,2],"C":[0,1,2,3]},"params":{"capacity[p]":"params['capacity_'+str(p)]","demand[c]":"params['demand_'+str(c)]","min_delivery[p]":"params['min_delivery_'+str(p)]","cost[p,c]":"params['cost_'+str(p)+'_'+str(c)]"},"variables":{"delivery[p,c]":"continuous >= 0","participates[p,c]":"binary"},"constraints":["sum_c delivery[p,c] <= capacity[p] for each p","sum_p delivery[p,c] >= demand[c] for each c","sum_p participates[p,c] >= 2 for each c","delivery[p,c] >= min_delivery[p]*participates[p,c] for each p,c","delivery[p,c] <= capacity[p]*participates[p,c] for each p,c"],"objective":"minimize sum_{p,c} cost[p,c]*delivery[p,c]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.producers = pyo.Set(initialize=range(3), ordered=True)
    model.contracts = pyo.Set(initialize=range(4), ordered=True)

    model.capacity = pyo.Param(
        model.producers,
        initialize={
            producer: params[f"capacity_{producer}"]
            for producer in model.producers
        },
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.contracts,
        initialize={
            contract: params[f"demand_{contract}"]
            for contract in model.contracts
        },
        within=pyo.NonNegativeReals,
    )
    model.min_delivery = pyo.Param(
        model.producers,
        initialize={
            producer: params[f"min_delivery_{producer}"]
            for producer in model.producers
        },
        within=pyo.NonNegativeReals,
    )
    model.unit_cost = pyo.Param(
        model.producers,
        model.contracts,
        initialize={
            (producer, contract): params[f"cost_{producer}_{contract}"]
            for producer in model.producers
            for contract in model.contracts
        },
        within=pyo.Reals,
    )

    model.delivery = pyo.Var(
        model.producers,
        model.contracts,
        domain=pyo.NonNegativeReals,
    )
    model.participates = pyo.Var(
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
            <= instance.capacity[producer]
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
            >= instance.demand[contract]
        )

    model.demand_requirements = pyo.Constraint(
        model.contracts, rule=demand_rule
    )

    def contributor_rule(instance, contract):
        return (
            sum(
                instance.participates[producer, contract]
                for producer in instance.producers
            )
            >= 2
        )

    model.contributor_requirements = pyo.Constraint(
        model.contracts, rule=contributor_rule
    )

    def minimum_delivery_rule(instance, producer, contract):
        return (
            instance.delivery[producer, contract]
            >= instance.min_delivery[producer]
            * instance.participates[producer, contract]
        )

    model.minimum_deliveries = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=minimum_delivery_rule,
    )

    def participation_link_rule(instance, producer, contract):
        return (
            instance.delivery[producer, contract]
            <= instance.capacity[producer]
            * instance.participates[producer, contract]
        )

    model.participation_links = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=participation_link_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[producer, contract]
            * model.delivery[producer, contract]
            for producer in model.producers
            for contract in model.contracts
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}