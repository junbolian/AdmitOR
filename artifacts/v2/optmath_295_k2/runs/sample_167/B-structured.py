# IR: {"sets":{"P":[0,1,2,3,4,5],"C":[0,1,2,3,4,5]},"params":{"cost":"real[P,C]","capacity":"nonnegative[P]","demand":"nonnegative[C]","min_contributors":"nonnegative_integer[C]","min_delivery":"nonnegative[P]"},"variables":{"delivery":"nonnegative_real[P,C]","contributes":"binary[P,C]"},"constraints":["capacity_limit[p]: sum(delivery[p,c] for c in C) <= capacity[p]","demand_requirement[c]: sum(delivery[p,c] for p in P) >= demand[c]","contributor_requirement[c]: sum(contributes[p,c] for p in P) >= min_contributors[c]","minimum_delivery[p,c]: delivery[p,c] >= min_delivery[p]*contributes[p,c]","delivery_link[p,c]: delivery[p,c] <= capacity[p]*contributes[p,c]"],"objective":"minimize sum(cost[p,c]*delivery[p,c] for p in P for c in C)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, 5)
    model.C = pyo.RangeSet(0, 5)

    model.cost = pyo.Param(
        model.P,
        model.C,
        initialize=lambda mdl, producer, contract: params["cost"][producer][contract],
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.P,
        initialize=lambda mdl, producer: params["capacity"][producer],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.C,
        initialize=lambda mdl, contract: params["demand"][contract],
        within=pyo.NonNegativeReals,
    )
    model.min_contributors = pyo.Param(
        model.C,
        initialize=lambda mdl, contract: params["min_contributors"][contract],
        within=pyo.NonNegativeIntegers,
    )
    model.min_delivery = pyo.Param(
        model.P,
        initialize=lambda mdl, producer: params["min_delivery"][producer],
        within=pyo.NonNegativeReals,
    )

    model.delivery = pyo.Var(
        model.P, model.C, domain=pyo.NonNegativeReals
    )
    model.contributes = pyo.Var(
        model.P, model.C, domain=pyo.Binary
    )

    model.capacity_limit = pyo.Constraint(
        model.P,
        rule=lambda mdl, producer: sum(
            mdl.delivery[producer, contract] for contract in mdl.C
        ) <= mdl.capacity[producer],
    )

    model.demand_requirement = pyo.Constraint(
        model.C,
        rule=lambda mdl, contract: sum(
            mdl.delivery[producer, contract] for producer in mdl.P
        ) >= mdl.demand[contract],
    )

    model.contributor_requirement = pyo.Constraint(
        model.C,
        rule=lambda mdl, contract: sum(
            mdl.contributes[producer, contract] for producer in mdl.P
        ) >= mdl.min_contributors[contract],
    )

    model.minimum_delivery = pyo.Constraint(
        model.P,
        model.C,
        rule=lambda mdl, producer, contract: (
            mdl.delivery[producer, contract]
            >= mdl.min_delivery[producer] * mdl.contributes[producer, contract]
        ),
    )

    model.delivery_link = pyo.Constraint(
        model.P,
        model.C,
        rule=lambda mdl, producer, contract: (
            mdl.delivery[producer, contract]
            <= mdl.capacity[producer] * mdl.contributes[producer, contract]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
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
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}