# IR: {"sets":{"P":[0,1,2,3,4,5],"C":[0,1,2,3,4,5]},"params":{"production_cost[P,C]":"real","producer_capacity[P]":"nonnegative real","contract_demand[C]":"nonnegative real","min_contributors[C]":"nonnegative integer","min_delivery_per_producer[P]":"nonnegative real"},"variables":{"delivery[P,C]":"nonnegative continuous","contributes[P,C]":"binary"},"constraints":["forall i: sum_j delivery[i,j] <= producer_capacity[i]","forall j: sum_i delivery[i,j] >= contract_demand[j]","forall j: sum_i contributes[i,j] >= min_contributors[j]","forall i,j: delivery[i,j] >= min_delivery_per_producer[i]*contributes[i,j]","forall i,j: delivery[i,j] <= producer_capacity[i]*contributes[i,j]"],"objective":"minimize sum_i sum_j production_cost[i,j]*delivery[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.producers = pyo.RangeSet(0, 5)
    model.contracts = pyo.RangeSet(0, 5)

    model.production_cost = pyo.Param(
        model.producers,
        model.contracts,
        initialize=lambda mdl, i, j: params["production_cost"][i][j],
        within=pyo.Reals,
    )
    model.producer_capacity = pyo.Param(
        model.producers,
        initialize=lambda mdl, i: params["producer_capacity"][i],
        within=pyo.NonNegativeReals,
    )
    model.contract_demand = pyo.Param(
        model.contracts,
        initialize=lambda mdl, j: params["contract_demand"][j],
        within=pyo.NonNegativeReals,
    )
    model.min_contributors = pyo.Param(
        model.contracts,
        initialize=lambda mdl, j: params["min_contributors"][j],
        within=pyo.NonNegativeIntegers,
    )
    model.min_delivery_per_producer = pyo.Param(
        model.producers,
        initialize=lambda mdl, i: params["min_delivery_per_producer"][i],
        within=pyo.NonNegativeReals,
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

    model.capacity_limits = pyo.Constraint(
        model.producers,
        rule=lambda mdl, i: sum(
            mdl.delivery[i, j] for j in mdl.contracts
        ) <= mdl.producer_capacity[i],
    )
    model.contract_fulfillment = pyo.Constraint(
        model.contracts,
        rule=lambda mdl, j: sum(
            mdl.delivery[i, j] for i in mdl.producers
        ) >= mdl.contract_demand[j],
    )
    model.contributor_requirements = pyo.Constraint(
        model.contracts,
        rule=lambda mdl, j: sum(
            mdl.contributes[i, j] for i in mdl.producers
        ) >= mdl.min_contributors[j],
    )
    model.minimum_delivery_links = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=lambda mdl, i, j: (
            mdl.delivery[i, j]
            >= mdl.min_delivery_per_producer[i] * mdl.contributes[i, j]
        ),
    )
    model.maximum_delivery_links = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=lambda mdl, i, j: (
            mdl.delivery[i, j]
            <= mdl.producer_capacity[i] * mdl.contributes[i, j]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.production_cost[i, j] * model.delivery[i, j]
            for i in model.producers
            for j in model.contracts
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Propagate unrelated runtime errors.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}