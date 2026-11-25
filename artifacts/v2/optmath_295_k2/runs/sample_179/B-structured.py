# IR: {"sets":{"P":[0,1,2,3,4,5],"C":[0,1,2,3,4,5]},"params":{"capacity[p]":"params['producer_capacity'][p]","demand[c]":"params['contract_demand'][c]","min_contributors[c]":"params['min_producers_per_contract'][c]","min_delivery[p]":"params['producer_min_delivery'][p]","cost_min":"params['cost_min']","cost_max":"params['cost_max']","cost_00":"params['cost_p0_c0']","cost_01":"params['cost_p0_c1']","cost[p,c]":"cost_00 if (p,c)==(0,0), cost_01 if (p,c)==(0,1), otherwise (cost_min+cost_max)/2"},"assumptions":["Unspecified pair costs equal the midpoint of the supplied cost range; the original problem does not specify their individual values."],"variables":{"delivery[p,c]":"nonnegative continuous","contributes[p,c]":"binary"},"constraints":["sum_c delivery[p,c] <= capacity[p] for each p","sum_p delivery[p,c] >= demand[c] for each c","sum_p contributes[p,c] >= min_contributors[c] for each c","delivery[p,c] >= min_delivery[p]*contributes[p,c] for each p,c","delivery[p,c] <= capacity[p]*contributes[p,c] for each p,c"],"objective":"minimize sum_p,c cost[p,c]*delivery[p,c]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using midpoint costs for producer-contract costs not supplied.

    Indexed input parameters must be sequences or mappings keyed by integers
    0 through 5. Individual unspecified costs cannot be recovered from their
    bounds; midpoint costs are an explicit modeling assumption.
    """
    producer_capacity = params["producer_capacity"]
    contract_demand = params["contract_demand"]
    min_producers_per_contract = params["min_producers_per_contract"]
    producer_min_delivery = params["producer_min_delivery"]
    cost_min = params["cost_min"]
    cost_max = params["cost_max"]
    cost_p0_c0 = params["cost_p0_c0"]
    cost_p0_c1 = params["cost_p0_c1"]

    model = pyo.ConcreteModel()
    model.producers = pyo.RangeSet(0, 5)
    model.contracts = pyo.RangeSet(0, 5)

    model.capacity = pyo.Param(
        model.producers,
        initialize={
            producer: producer_capacity[producer]
            for producer in model.producers
        },
    )
    model.demand = pyo.Param(
        model.contracts,
        initialize={
            contract: contract_demand[contract]
            for contract in model.contracts
        },
    )
    model.minimum_contributors = pyo.Param(
        model.contracts,
        initialize={
            contract: min_producers_per_contract[contract]
            for contract in model.contracts
        },
    )
    model.minimum_delivery = pyo.Param(
        model.producers,
        initialize={
            producer: producer_min_delivery[producer]
            for producer in model.producers
        },
    )

    midpoint_cost = (cost_min + cost_max) / 2
    costs = {
        (producer, contract): midpoint_cost
        for producer in model.producers
        for contract in model.contracts
    }
    costs[0, 0] = cost_p0_c0
    costs[0, 1] = cost_p0_c1
    model.unit_cost = pyo.Param(
        model.producers, model.contracts, initialize=costs
    )

    model.delivery = pyo.Var(
        model.producers, model.contracts, domain=pyo.NonNegativeReals
    )
    model.contributes = pyo.Var(
        model.producers, model.contracts, domain=pyo.Binary
    )

    def capacity_rule(model, producer):
        return sum(
            model.delivery[producer, contract]
            for contract in model.contracts
        ) <= model.capacity[producer]

    model.capacity_limits = pyo.Constraint(
        model.producers, rule=capacity_rule
    )

    def fulfillment_rule(model, contract):
        return sum(
            model.delivery[producer, contract]
            for producer in model.producers
        ) >= model.demand[contract]

    model.contract_fulfillment = pyo.Constraint(
        model.contracts, rule=fulfillment_rule
    )

    def contributors_rule(model, contract):
        return sum(
            model.contributes[producer, contract]
            for producer in model.producers
        ) >= model.minimum_contributors[contract]

    model.contributor_requirements = pyo.Constraint(
        model.contracts, rule=contributors_rule
    )

    def minimum_delivery_rule(model, producer, contract):
        return (
            model.delivery[producer, contract]
            >= model.minimum_delivery[producer]
            * model.contributes[producer, contract]
        )

    model.delivery_minimums = pyo.Constraint(
        model.producers, model.contracts, rule=minimum_delivery_rule
    )

    def contribution_link_rule(model, producer, contract):
        return (
            model.delivery[producer, contract]
            <= model.capacity[producer]
            * model.contributes[producer, contract]
        )

    model.contribution_links = pyo.Constraint(
        model.producers, model.contracts, rule=contribution_link_rule
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
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}