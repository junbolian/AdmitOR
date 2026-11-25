# IR: {"sets":{"P":"0..5","C":"0..6"},"params":{"producer_capacity":"P -> nonnegative real","contract_demand":"C -> nonnegative real","min_contributors":"C -> nonnegative integer, frozen","producer_min_delivery":"P -> nonnegative real","cost_matrix":"P x C -> real"},"variables":{"delivery":"P x C -> nonnegative real","contributes":"P x C -> binary"},"constraints":["For each i in P: sum(delivery[i,j] for j in C) <= producer_capacity[i]","For each j in C: sum(delivery[i,j] for i in P) >= contract_demand[j]","For each j in C: sum(contributes[i,j] for i in P) >= min_contributors[j]","For each (i,j): delivery[i,j] >= producer_min_delivery[i]*contributes[i,j]","For each (i,j): delivery[i,j] <= producer_capacity[i]*contributes[i,j]"],"objective":"Minimize sum(cost_matrix[i,j]*delivery[i,j] for i in P, j in C)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    producer_capacity = params["producer_capacity"]
    contract_demand = params["contract_demand"]
    min_contributors = params["min_contributors"]
    producer_min_delivery = params["producer_min_delivery"]
    cost_matrix = params["cost_matrix"]

    model = pyo.ConcreteModel()

    model.producers = pyo.RangeSet(0, 5)
    model.contracts = pyo.RangeSet(0, 6)

    model.producer_capacity = pyo.Param(
        model.producers,
        initialize=lambda model, i: producer_capacity[i],
        within=pyo.NonNegativeReals,
    )
    model.contract_demand = pyo.Param(
        model.contracts,
        initialize=lambda model, j: contract_demand[j],
        within=pyo.NonNegativeReals,
    )
    model.min_contributors = pyo.Param(
        model.contracts,
        initialize=lambda model, j: min_contributors[j],
        within=pyo.NonNegativeIntegers,
        mutable=False,
    )
    model.producer_min_delivery = pyo.Param(
        model.producers,
        initialize=lambda model, i: producer_min_delivery[i],
        within=pyo.NonNegativeReals,
    )
    model.cost_matrix = pyo.Param(
        model.producers,
        model.contracts,
        initialize=lambda model, i, j: cost_matrix[i][j],
        within=pyo.Reals,
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

    def capacity_rule(model, i):
        return (
            sum(model.delivery[i, j] for j in model.contracts)
            <= model.producer_capacity[i]
        )

    model.capacity_constraints = pyo.Constraint(
        model.producers,
        rule=capacity_rule,
    )

    def demand_rule(model, j):
        return (
            sum(model.delivery[i, j] for i in model.producers)
            >= model.contract_demand[j]
        )

    model.demand_constraints = pyo.Constraint(
        model.contracts,
        rule=demand_rule,
    )

    def contributor_rule(model, j):
        return (
            sum(model.contributes[i, j] for i in model.producers)
            >= model.min_contributors[j]
        )

    model.contributor_constraints = pyo.Constraint(
        model.contracts,
        rule=contributor_rule,
    )

    def minimum_delivery_rule(model, i, j):
        return (
            model.delivery[i, j]
            >= model.producer_min_delivery[i] * model.contributes[i, j]
        )

    model.minimum_delivery_constraints = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=minimum_delivery_rule,
    )

    def delivery_activation_rule(model, i, j):
        return (
            model.delivery[i, j]
            <= model.producer_capacity[i] * model.contributes[i, j]
        )

    model.delivery_activation_constraints = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=delivery_activation_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost_matrix[i, j] * model.delivery[i, j]
            for i in model.producers
            for j in model.contracts
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPSI raises this when it cannot load a feasible solution.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}