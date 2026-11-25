# IR: {"sets":{"P":[0,1,2,3,4],"C":[0,1,2,3,4,5,6]},"params":{"cost":"real[P,C]","capacity":"nonnegative[P]","demand":"nonnegative[C]","min_delivery":"positive[P]","min_contributors":"nonnegative_integer[C]"},"variables":{"delivery[P,C]":"nonnegative_real","contributes[P,C]":"binary"},"constraints":["forall i in P: sum(j in C, delivery[i,j]) <= capacity[i]","forall j in C: sum(i in P, delivery[i,j]) >= demand[j]","forall i in P,j in C: delivery[i,j] >= min_delivery[i]*contributes[i,j]","forall i in P,j in C: delivery[i,j] <= capacity[i]*contributes[i,j]","forall j in C: sum(i in P, contributes[i,j]) >= min_contributors[j]"],"objective":"minimize sum(i in P,j in C, cost[i,j]*delivery[i,j])"}

import pyomo.environ as pyo
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

    model.unit_cost = pyo.Param(
        model.producers,
        model.contracts,
        initialize=lambda mdl, i, j: cost[i][j],
        within=pyo.Reals,
    )
    model.producer_capacity = pyo.Param(
        model.producers,
        initialize=lambda mdl, i: capacity[i],
        within=pyo.NonNegativeReals,
    )
    model.contract_demand = pyo.Param(
        model.contracts,
        initialize=lambda mdl, j: demand[j],
        within=pyo.NonNegativeReals,
    )
    model.minimum_delivery = pyo.Param(
        model.producers,
        initialize=lambda mdl, i: min_delivery[i],
        within=pyo.PositiveReals,
    )
    model.required_contributors = pyo.Param(
        model.contracts,
        initialize=lambda mdl, j: min_contributors[j],
        within=pyo.NonNegativeIntegers,
    )

    model.delivery = pyo.Var(
        model.producers, model.contracts, within=pyo.NonNegativeReals
    )
    model.contributes = pyo.Var(
        model.producers, model.contracts, within=pyo.Binary
    )

    model.capacity_limits = pyo.Constraint(
        model.producers,
        rule=lambda mdl, i: sum(
            mdl.delivery[i, j] for j in mdl.contracts
        ) <= mdl.producer_capacity[i],
    )
    model.demand_requirements = pyo.Constraint(
        model.contracts,
        rule=lambda mdl, j: sum(
            mdl.delivery[i, j] for i in mdl.producers
        ) >= mdl.contract_demand[j],
    )
    model.minimum_delivery_links = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=lambda mdl, i, j: (
            mdl.delivery[i, j]
            >= mdl.minimum_delivery[i] * mdl.contributes[i, j]
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
    model.contributor_requirements = pyo.Constraint(
        model.contracts,
        rule=lambda mdl, j: sum(
            mdl.contributes[i, j] for i in mdl.producers
        ) >= mdl.required_contributors[j],
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[i, j] * model.delivery[i, j]
            for i in model.producers
            for j in model.contracts
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