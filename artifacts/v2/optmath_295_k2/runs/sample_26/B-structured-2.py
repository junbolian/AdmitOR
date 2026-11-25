# IR: {"sets":{"P":[0,1,2,3],"C":[0,1,2,3]},"params":{"capacity":"P -> nonnegative real, from params['capacity']","demand":"C -> nonnegative real, from params['demand']","min_delivery":"P -> nonnegative real, from params['min_delivery']","cost":"P x C -> real, from params['cost'][p][c]"},"variables":{"delivery[p,c]":"nonnegative continuous","contributes[p,c]":"binary"},"constraints":["sum(c in C, delivery[p,c]) <= capacity[p] for p in P","sum(p in P, delivery[p,c]) >= demand[c] for c in C","sum(p in P, contributes[p,c]) >= 2 for c in C","delivery[p,c] >= min_delivery[p]*contributes[p,c] for (p,c) in P x C","delivery[p,c] <= capacity[p]*contributes[p,c] for (p,c) in P x C"],"objective":"minimize sum((p,c) in P x C, cost[p,c]*delivery[p,c])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, 3)
    model.C = pyo.RangeSet(0, 3)

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
    model.min_delivery = pyo.Param(
        model.P,
        initialize=lambda mdl, producer: params["min_delivery"][producer],
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.P,
        model.C,
        initialize=lambda mdl, producer, contract: params["cost"][producer][contract],
        within=pyo.Reals,
    )

    model.delivery = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    model.contributes = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def capacity_rule(mdl, producer):
        return (
            sum(mdl.delivery[producer, contract] for contract in mdl.C)
            <= mdl.capacity[producer]
        )

    model.capacity_limit = pyo.Constraint(model.P, rule=capacity_rule)

    def demand_rule(mdl, contract):
        return (
            sum(mdl.delivery[producer, contract] for producer in mdl.P)
            >= mdl.demand[contract]
        )

    model.demand_requirement = pyo.Constraint(model.C, rule=demand_rule)

    def contributor_rule(mdl, contract):
        return (
            sum(mdl.contributes[producer, contract] for producer in mdl.P)
            >= 2
        )

    model.contributor_requirement = pyo.Constraint(
        model.C, rule=contributor_rule
    )

    def minimum_delivery_rule(mdl, producer, contract):
        return (
            mdl.delivery[producer, contract]
            >= mdl.min_delivery[producer] * mdl.contributes[producer, contract]
        )

    model.minimum_delivery_link = pyo.Constraint(
        model.P, model.C, rule=minimum_delivery_rule
    )

    def activation_rule(mdl, producer, contract):
        return (
            mdl.delivery[producer, contract]
            <= mdl.capacity[producer] * mdl.contributes[producer, contract]
        )

    model.delivery_activation = pyo.Constraint(
        model.P, model.C, rule=activation_rule
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