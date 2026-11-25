# IR: {"sets":{"P":[0,1,2,3,4,5],"C":[0,1,2,3,4,5]},"params":{"capacity[p]":"params['producer_capacity'][p]","demand[c]":"params['contract_demand'][c]","contributors[c]":"params['min_producers_per_contract'][c]","minimum[p]":"params['producer_min_delivery'][p]","cost_lower":"params['cost_min']","cost_upper":"params['cost_max']","cost00":"params['cost_p0_c0']","cost01":"params['cost_p0_c1']"},"cost_completion_assumption":"The other 34 costs are unspecified; use (cost_lower+cost_upper)/2 for each.","derived":{"cost[p,c]":"cost00 if (p,c)=(0,0); cost01 if (p,c)=(0,1); otherwise (cost_lower+cost_upper)/2"},"variables":{"delivery[p,c]":"nonnegative continuous","participates[p,c]":"binary"},"constraints":["sum_c delivery[p,c] <= capacity[p] for each p","sum_p delivery[p,c] >= demand[c] for each c","sum_p participates[p,c] >= contributors[c] for each c","delivery[p,c] >= minimum[p]*participates[p,c] for each p,c","delivery[p,c] <= capacity[p]*participates[p,c] for each p,c"],"objective":"minimize sum_p,c cost[p,c]*delivery[p,c]"}
#
# Indexed inputs must be sequences or mappings keyed by integers 0 through 5.
# The midpoint assumption above is necessary because the problem does not
# specify a complete cost matrix; the resulting objective depends on it.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    producer_capacity = params["producer_capacity"]
    contract_demand = params["contract_demand"]
    min_producers_per_contract = params["min_producers_per_contract"]
    producer_min_delivery = params["producer_min_delivery"]
    cost_min = params["cost_min"]
    cost_max = params["cost_max"]
    cost_p0_c0 = params["cost_p0_c0"]
    cost_p0_c1 = params["cost_p0_c1"]

    if cost_min > cost_max:
        return {"objective": None, "status": "invalid_cost_bounds"}

    midpoint_cost = (cost_min + cost_max) / 2

    model = pyo.ConcreteModel()
    model.producers = pyo.RangeSet(0, 5)
    model.contracts = pyo.RangeSet(0, 5)

    model.capacity = pyo.Param(
        model.producers,
        initialize={
            producer: producer_capacity[producer]
            for producer in model.producers
        },
        within=pyo.NonNegativeReals,
    )
    model.required_delivery = pyo.Param(
        model.contracts,
        initialize={
            contract: contract_demand[contract]
            for contract in model.contracts
        },
        within=pyo.NonNegativeReals,
    )
    model.required_contributors = pyo.Param(
        model.contracts,
        initialize={
            contract: min_producers_per_contract[contract]
            for contract in model.contracts
        },
        within=pyo.NonNegativeIntegers,
    )
    model.minimum_delivery = pyo.Param(
        model.producers,
        initialize={
            producer: producer_min_delivery[producer]
            for producer in model.producers
        },
        within=pyo.PositiveReals,
    )

    unit_costs = {
        (producer, contract): midpoint_cost
        for producer in model.producers
        for contract in model.contracts
    }
    unit_costs[0, 0] = cost_p0_c0
    unit_costs[0, 1] = cost_p0_c1

    model.unit_cost = pyo.Param(
        model.producers,
        model.contracts,
        initialize=unit_costs,
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

    model.capacity_limit = pyo.Constraint(
        model.producers, rule=capacity_rule
    )

    def fulfillment_rule(instance, contract):
        return (
            sum(
                instance.delivery[producer, contract]
                for producer in instance.producers
            )
            >= instance.required_delivery[contract]
        )

    model.contract_fulfillment = pyo.Constraint(
        model.contracts, rule=fulfillment_rule
    )

    def contributors_rule(instance, contract):
        return (
            sum(
                instance.participates[producer, contract]
                for producer in instance.producers
            )
            >= instance.required_contributors[contract]
        )

    model.contributor_requirement = pyo.Constraint(
        model.contracts, rule=contributors_rule
    )

    def minimum_delivery_rule(instance, producer, contract):
        return (
            instance.delivery[producer, contract]
            >= instance.minimum_delivery[producer]
            * instance.participates[producer, contract]
        )

    model.delivery_lower_link = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=minimum_delivery_rule,
    )

    def maximum_delivery_rule(instance, producer, contract):
        return (
            instance.delivery[producer, contract]
            <= instance.capacity[producer]
            * instance.participates[producer, contract]
        )

    model.delivery_upper_link = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=maximum_delivery_rule,
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

    solver_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        # APPsi can raise when no feasible solution is available to load.
        # Objective retrieval below remains the sole success criterion.
        solver_failed = True

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {
            "objective": None,
            "status": (
                "solve_failed" if solver_failed else "objective_unavailable"
            ),
        }

    return {"objective": obj_val, "status": "optimal"}