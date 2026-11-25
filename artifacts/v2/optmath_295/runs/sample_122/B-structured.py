# IR: {"sets":{"P":[0,1,2,3,4,5],"C":[0,1,2,3,4,5]},"params":{"production_cost":"real[P,C]","producer_capacity":"nonnegative[P]","contract_demand":"nonnegative[C]","min_contributors":"nonnegative_integer[C]","min_delivery_per_producer":"nonnegative[P]"},"variables":{"delivery":"nonnegative_real[P,C]","contributes":"binary[P,C]"},"constraints":["sum(c in C, delivery[p,c]) <= producer_capacity[p] for p in P","sum(p in P, delivery[p,c]) >= contract_demand[c] for c in C","sum(p in P, contributes[p,c]) >= min_contributors[c] for c in C","delivery[p,c] >= min_delivery_per_producer[p]*contributes[p,c] for p in P,c in C","delivery[p,c] <= producer_capacity[p]*contributes[p,c] for p in P,c in C"],"objective":"minimize sum(p in P,c in C, production_cost[p,c]*delivery[p,c])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.producers = pyo.RangeSet(0, 5)
    model.contracts = pyo.RangeSet(0, 5)

    model.production_cost = pyo.Param(
        model.producers,
        model.contracts,
        initialize=lambda mdl, producer, contract: (
            params["production_cost"][producer][contract]
        ),
        within=pyo.Reals,
    )
    model.producer_capacity = pyo.Param(
        model.producers,
        initialize=lambda mdl, producer: params["producer_capacity"][producer],
        within=pyo.NonNegativeReals,
    )
    model.contract_demand = pyo.Param(
        model.contracts,
        initialize=lambda mdl, contract: params["contract_demand"][contract],
        within=pyo.NonNegativeReals,
    )
    model.min_contributors = pyo.Param(
        model.contracts,
        initialize=lambda mdl, contract: params["min_contributors"][contract],
        within=pyo.NonNegativeIntegers,
    )
    model.min_delivery_per_producer = pyo.Param(
        model.producers,
        initialize=lambda mdl, producer: (
            params["min_delivery_per_producer"][producer]
        ),
        within=pyo.NonNegativeReals,
    )

    model.delivery = pyo.Var(
        model.producers, model.contracts, domain=pyo.NonNegativeReals
    )
    model.contributes = pyo.Var(
        model.producers, model.contracts, domain=pyo.Binary
    )

    model.capacity_limits = pyo.Constraint(
        model.producers,
        rule=lambda mdl, producer: sum(
            mdl.delivery[producer, contract] for contract in mdl.contracts
        ) <= mdl.producer_capacity[producer],
    )
    model.contract_fulfillment = pyo.Constraint(
        model.contracts,
        rule=lambda mdl, contract: sum(
            mdl.delivery[producer, contract] for producer in mdl.producers
        ) >= mdl.contract_demand[contract],
    )
    model.contributor_requirements = pyo.Constraint(
        model.contracts,
        rule=lambda mdl, contract: sum(
            mdl.contributes[producer, contract] for producer in mdl.producers
        ) >= mdl.min_contributors[contract],
    )
    model.minimum_delivery_links = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=lambda mdl, producer, contract: (
            mdl.delivery[producer, contract]
            >= mdl.min_delivery_per_producer[producer]
            * mdl.contributes[producer, contract]
        ),
    )
    model.maximum_delivery_links = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=lambda mdl, producer, contract: (
            mdl.delivery[producer, contract]
            <= mdl.producer_capacity[producer]
            * mdl.contributes[producer, contract]
        ),
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
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}