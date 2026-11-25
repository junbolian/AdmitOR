# IR: {"sets":{"P":[0,1,2,3,4],"C":[0,1,2,3,4,5,6]},"params":{"cost":"real[P,C]","capacity":"nonnegative[P]","demand":"nonnegative[C]","min_delivery":"nonnegative[P]","min_contributors":"nonnegative_integer[C]"},"variables":{"delivery[P,C]":"nonnegative_continuous","contributes[P,C]":"binary"},"constraints":["sum(delivery[p,c] for c in C) <= capacity[p] for p in P","sum(delivery[p,c] for p in P) >= demand[c] for c in C","delivery[p,c] >= min_delivery[p]*contributes[p,c] for p in P,c in C","delivery[p,c] <= capacity[p]*contributes[p,c] for p in P,c in C","sum(contributes[p,c] for p in P) >= min_contributors[c] for c in C"],"objective":"minimize sum(cost[p,c]*delivery[p,c] for p in P,c in C)"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    min_delivery = params["min_delivery"]
    min_contributors = params["min_contributors"]

    model = pyo.ConcreteModel()

    model.producers = pyo.RangeSet(0, 4)
    model.contracts = pyo.RangeSet(0, 6)

    model.production_cost = pyo.Param(
        model.producers,
        model.contracts,
        initialize=lambda mdl, producer, contract: cost[producer][contract],
        within=pyo.Reals,
    )
    model.producer_capacity = pyo.Param(
        model.producers,
        initialize=lambda mdl, producer: capacity[producer],
        within=pyo.NonNegativeReals,
    )
    model.contract_demand = pyo.Param(
        model.contracts,
        initialize=lambda mdl, contract: demand[contract],
        within=pyo.NonNegativeReals,
    )
    model.minimum_delivery = pyo.Param(
        model.producers,
        initialize=lambda mdl, producer: min_delivery[producer],
        within=pyo.NonNegativeReals,
    )
    model.minimum_contributors = pyo.Param(
        model.contracts,
        initialize=lambda mdl, contract: min_contributors[contract],
        within=pyo.NonNegativeIntegers,
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

    def capacity_rule(mdl, producer):
        return (
            sum(mdl.delivery[producer, contract] for contract in mdl.contracts)
            <= mdl.producer_capacity[producer]
        )

    model.capacity_limits = pyo.Constraint(
        model.producers, rule=capacity_rule
    )

    def demand_rule(mdl, contract):
        return (
            sum(mdl.delivery[producer, contract] for producer in mdl.producers)
            >= mdl.contract_demand[contract]
        )

    model.demand_requirements = pyo.Constraint(
        model.contracts, rule=demand_rule
    )

    def minimum_delivery_rule(mdl, producer, contract):
        return (
            mdl.delivery[producer, contract]
            >= mdl.minimum_delivery[producer]
            * mdl.contributes[producer, contract]
        )

    model.participation_lower_bounds = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=minimum_delivery_rule,
    )

    def participation_upper_rule(mdl, producer, contract):
        return (
            mdl.delivery[producer, contract]
            <= mdl.producer_capacity[producer]
            * mdl.contributes[producer, contract]
        )

    model.participation_upper_bounds = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=participation_upper_rule,
    )

    def contributors_rule(mdl, contract):
        return (
            sum(
                mdl.contributes[producer, contract]
                for producer in mdl.producers
            )
            >= mdl.minimum_contributors[contract]
        )

    model.contributor_requirements = pyo.Constraint(
        model.contracts, rule=contributors_rule
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

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}