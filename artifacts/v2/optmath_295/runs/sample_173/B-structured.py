# IR: {"sets":{"P":"0..len(producer_capacity)-1","C":"0..len(contract_demand)-1"},"params":{"producer_capacity":"capacity[P]","contract_demand":"demand[C]","min_producers_per_contract":"scalar integer","min_delivery_per_producer":"minimum_delivery[P]","production_cost":"cost[P,C]"},"variables":{"delivery[P,C]":"nonnegative continuous","contributes[P,C]":"binary"},"constraints":["sum(delivery[p,c] for c in C) <= capacity[p] for p in P","sum(delivery[p,c] for p in P) >= demand[c] for c in C","sum(contributes[p,c] for p in P) >= min_producers_per_contract for c in C","delivery[p,c] >= minimum_delivery[p]*contributes[p,c] for (p,c) in P x C","delivery[p,c] <= capacity[p]*contributes[p,c] for (p,c) in P x C"],"objective":"minimize sum(cost[p,c]*delivery[p,c] for (p,c) in P x C)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    producer_capacity = params["producer_capacity"]
    contract_demand = params["contract_demand"]
    min_producers_per_contract = params["min_producers_per_contract"]
    min_delivery_per_producer = params["min_delivery_per_producer"]
    production_cost = params["production_cost"]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(
        initialize=range(len(producer_capacity)), ordered=True
    )
    model.C = pyo.Set(
        initialize=range(len(contract_demand)), ordered=True
    )

    model.capacity = pyo.Param(
        model.P,
        initialize=lambda mdl, producer: producer_capacity[producer],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.C,
        initialize=lambda mdl, contract: contract_demand[contract],
        within=pyo.NonNegativeReals,
    )
    model.required_contributors = pyo.Param(
        initialize=min_producers_per_contract,
        within=pyo.NonNegativeIntegers,
    )
    model.minimum_delivery = pyo.Param(
        model.P,
        initialize=lambda mdl, producer: min_delivery_per_producer[producer],
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.P,
        model.C,
        initialize=lambda mdl, producer, contract: (
            production_cost[producer][contract]
        ),
        within=pyo.Reals,
    )

    model.delivery = pyo.Var(
        model.P, model.C, domain=pyo.NonNegativeReals
    )
    model.contributes = pyo.Var(
        model.P, model.C, domain=pyo.Binary
    )

    def capacity_rule(mdl, producer):
        return (
            pyo.quicksum(mdl.delivery[producer, contract] for contract in mdl.C)
            <= mdl.capacity[producer]
        )

    model.capacity_limit = pyo.Constraint(model.P, rule=capacity_rule)

    def demand_rule(mdl, contract):
        return (
            pyo.quicksum(mdl.delivery[producer, contract] for producer in mdl.P)
            >= mdl.demand[contract]
        )

    model.demand_requirement = pyo.Constraint(model.C, rule=demand_rule)

    def contributor_rule(mdl, contract):
        return (
            pyo.quicksum(
                mdl.contributes[producer, contract] for producer in mdl.P
            )
            >= mdl.required_contributors
        )

    model.contributor_requirement = pyo.Constraint(
        model.C, rule=contributor_rule
    )

    def minimum_delivery_rule(mdl, producer, contract):
        return (
            mdl.delivery[producer, contract]
            >= mdl.minimum_delivery[producer]
            * mdl.contributes[producer, contract]
        )

    model.delivery_lower_link = pyo.Constraint(
        model.P, model.C, rule=minimum_delivery_rule
    )

    def maximum_delivery_rule(mdl, producer, contract):
        return (
            mdl.delivery[producer, contract]
            <= mdl.capacity[producer] * mdl.contributes[producer, contract]
        )

    model.delivery_upper_link = pyo.Constraint(
        model.P, model.C, rule=maximum_delivery_rule
    )

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.cost[producer, contract] * model.delivery[producer, contract]
            for producer in model.P
            for contract in model.C
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