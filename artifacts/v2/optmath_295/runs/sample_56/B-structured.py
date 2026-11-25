# IR: {"sets":{"P":[0,1,2],"C":[0,1,2,3]},"params":{"capacity":"capacity[p]","demand":"demand[c]","min_delivery":"min_delivery[p]","cost":"cost[p][c]"},"variables":{"delivery[p,c]":"nonnegative continuous","contributes[p,c]":"binary"},"constraints":["sum(c in C, delivery[p,c]) <= capacity[p] for p in P","sum(p in P, delivery[p,c]) >= demand[c] for c in C","sum(p in P, contributes[p,c]) >= 2 for c in C","delivery[p,c] >= min_delivery[p]*contributes[p,c] for p in P,c in C","delivery[p,c] <= capacity[p]*contributes[p,c] for p in P,c in C"],"objective":"minimize sum(p in P,c in C,cost[p][c]*delivery[p,c])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using producer-indexed vectors and a producer-by-contract cost matrix."""
    capacity = params["capacity"]
    demand = params["demand"]
    min_delivery = params["min_delivery"]
    cost = params["cost"]

    model = pyo.ConcreteModel()

    model.producers = pyo.RangeSet(0, 2)
    model.contracts = pyo.RangeSet(0, 3)

    model.capacity = pyo.Param(
        model.producers,
        initialize=lambda mdl, producer: capacity[producer],
    )
    model.demand = pyo.Param(
        model.contracts,
        initialize=lambda mdl, contract: demand[contract],
    )
    model.min_delivery = pyo.Param(
        model.producers,
        initialize=lambda mdl, producer: min_delivery[producer],
    )
    model.cost = pyo.Param(
        model.producers,
        model.contracts,
        initialize=lambda mdl, producer, contract: cost[producer][contract],
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

    def producer_capacity_rule(mdl, producer):
        return (
            sum(mdl.delivery[producer, contract] for contract in mdl.contracts)
            <= mdl.capacity[producer]
        )

    model.producer_capacity_limit = pyo.Constraint(
        model.producers, rule=producer_capacity_rule
    )

    def contract_demand_rule(mdl, contract):
        return (
            sum(mdl.delivery[producer, contract] for producer in mdl.producers)
            >= mdl.demand[contract]
        )

    model.contract_demand_requirement = pyo.Constraint(
        model.contracts, rule=contract_demand_rule
    )

    def producer_count_rule(mdl, contract):
        return (
            sum(mdl.contributes[producer, contract] for producer in mdl.producers)
            >= 2
        )

    model.contract_producer_requirement = pyo.Constraint(
        model.contracts, rule=producer_count_rule
    )

    def minimum_delivery_rule(mdl, producer, contract):
        return (
            mdl.delivery[producer, contract]
            >= mdl.min_delivery[producer] * mdl.contributes[producer, contract]
        )

    model.minimum_delivery_requirement = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=minimum_delivery_rule,
    )

    def contribution_link_rule(mdl, producer, contract):
        return (
            mdl.delivery[producer, contract]
            <= mdl.capacity[producer] * mdl.contributes[producer, contract]
        )

    model.contribution_delivery_limit = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=contribution_link_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[producer, contract] * model.delivery[producer, contract]
            for producer in model.producers
            for contract in model.contracts
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
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}