# IR: {"sets":{"P":[0,1,2,3,4],"C":[0,1,2,3,4,5]},"params":{"capacity":"P -> nonnegative real","demand":"C -> nonnegative real","cost":"P x C -> real","min_delivery":"P -> nonnegative real","min_contributors":"C -> nonnegative integer"},"variables":{"delivery[p,c]":"nonnegative continuous","contributes[p,c]":"binary"},"constraints":["sum(c in C) delivery[p,c] <= capacity[p] for each p in P","sum(p in P) delivery[p,c] >= demand[c] for each c in C","delivery[p,c] >= min_delivery[p]*contributes[p,c] for each (p,c) in P x C","delivery[p,c] <= capacity[p]*contributes[p,c] for each (p,c) in P x C","sum(p in P) contributes[p,c] >= min_contributors[c] for each c in C"],"objective":"minimize sum((p,c) in P x C) cost[p,c]*delivery[p,c]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Read indexed parameters from sequences or integer-keyed mappings.

    The cost parameter must support cost[producer][contract].
    """
    model = pyo.ConcreteModel()

    model.producers = pyo.RangeSet(0, 4)
    model.contracts = pyo.RangeSet(0, 5)

    model.capacity = pyo.Param(
        model.producers,
        initialize=lambda mdl, producer: params["capacity"][producer],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.contracts,
        initialize=lambda mdl, contract: params["demand"][contract],
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.producers,
        model.contracts,
        initialize=lambda mdl, producer, contract: params["cost"][producer][contract],
        within=pyo.Reals,
    )
    model.min_delivery = pyo.Param(
        model.producers,
        initialize=lambda mdl, producer: params["min_delivery"][producer],
        within=pyo.NonNegativeReals,
    )
    model.min_contributors = pyo.Param(
        model.contracts,
        initialize=lambda mdl, contract: params["min_contributors"][contract],
        within=pyo.NonNegativeIntegers,
    )

    model.delivery = pyo.Var(
        model.producers, model.contracts, domain=pyo.NonNegativeReals
    )
    model.contributes = pyo.Var(
        model.producers, model.contracts, domain=pyo.Binary
    )

    model.producer_capacity = pyo.Constraint(
        model.producers,
        rule=lambda mdl, producer: sum(
            mdl.delivery[producer, contract] for contract in mdl.contracts
        )
        <= mdl.capacity[producer],
    )

    model.contract_demand = pyo.Constraint(
        model.contracts,
        rule=lambda mdl, contract: sum(
            mdl.delivery[producer, contract] for producer in mdl.producers
        )
        >= mdl.demand[contract],
    )

    model.minimum_delivery = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=lambda mdl, producer, contract: mdl.delivery[producer, contract]
        >= mdl.min_delivery[producer] * mdl.contributes[producer, contract],
    )

    model.delivery_activation = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=lambda mdl, producer, contract: mdl.delivery[producer, contract]
        <= mdl.capacity[producer] * mdl.contributes[producer, contract],
    )

    model.contributor_requirement = pyo.Constraint(
        model.contracts,
        rule=lambda mdl, contract: sum(
            mdl.contributes[producer, contract] for producer in mdl.producers
        )
        >= mdl.min_contributors[contract],
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
    except RuntimeError as error:
        # Appsi raises this when automatic solution loading finds no solution.
        # Leave success determination to objective evaluation below.
        if "A feasible solution was not found" not in str(error):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}