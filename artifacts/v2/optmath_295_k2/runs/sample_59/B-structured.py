# IR: {"sets":{"T":[1,2,3,4,5,6],"S":[0,1,2,3,4,5,6]},"params":{"fixed_setup_cost":"T -> real, from params","variable_production_cost":"T -> real, from params","inventory_holding_cost":"T -> real, from params","backlogging_cost":"T -> real, from params","demand":"T -> nonnegative real, from params","production_capacity":"nonnegative real scalar, from params"},"variables":{"setup":"T -> binary","production":"T -> nonnegative real","inventory":"S -> nonnegative real","backlog":"S -> nonnegative real"},"constraints":["inventory[t-1] - backlog[t-1] + production[t] = demand[t] + inventory[t] - backlog[t], for t in T","production[t] <= production_capacity * setup[t], for t in T","inventory[0] = inventory[6] = 0","backlog[0] = backlog[6] = 0"],"objective":"minimize sum(fixed_setup_cost[t]*setup[t] + variable_production_cost[t]*production[t] + inventory_holding_cost[t]*inventory[t] + backlogging_cost[t]*backlog[t] for t in T)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept period data as six-element sequences or mappings keyed by 1..6."""

    periods = range(1, 7)

    def period_data(values):
        if isinstance(values, Mapping):
            return {t: values[t] for t in periods}
        if len(values) != 6:
            raise ValueError("Period parameter sequences must contain six values.")
        return {t: values[t - 1] for t in periods}

    model = pyo.ConcreteModel()
    model.T = pyo.RangeSet(1, 6)
    model.S = pyo.RangeSet(0, 6)

    model.fixed_setup_cost = pyo.Param(
        model.T,
        initialize=period_data(params["fixed_setup_cost"]),
        within=pyo.Reals,
    )
    model.variable_production_cost = pyo.Param(
        model.T,
        initialize=period_data(params["variable_production_cost"]),
        within=pyo.Reals,
    )
    model.inventory_holding_cost = pyo.Param(
        model.T,
        initialize=period_data(params["inventory_holding_cost"]),
        within=pyo.Reals,
    )
    model.backlogging_cost = pyo.Param(
        model.T,
        initialize=period_data(params["backlogging_cost"]),
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.T,
        initialize=period_data(params["demand"]),
        within=pyo.NonNegativeReals,
    )
    model.production_capacity = pyo.Param(
        initialize=params["production_capacity"],
        within=pyo.NonNegativeReals,
    )

    model.setup = pyo.Var(model.T, domain=pyo.Binary)
    model.production = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.S, domain=pyo.NonNegativeReals)
    model.backlog = pyo.Var(model.S, domain=pyo.NonNegativeReals)

    model.inventory[0].fix(0)
    model.inventory[6].fix(0)
    model.backlog[0].fix(0)
    model.backlog[6].fix(0)

    def balance_rule(instance, t):
        return (
            instance.inventory[t - 1]
            - instance.backlog[t - 1]
            + instance.production[t]
            == instance.demand[t]
            + instance.inventory[t]
            - instance.backlog[t]
        )

    model.demand_balance = pyo.Constraint(model.T, rule=balance_rule)

    def capacity_rule(instance, t):
        return (
            instance.production[t]
            <= instance.production_capacity * instance.setup[t]
        )

    model.capacity_limit = pyo.Constraint(model.T, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_setup_cost[t] * model.setup[t]
            + model.variable_production_cost[t] * model.production[t]
            + model.inventory_holding_cost[t] * model.inventory[t]
            + model.backlogging_cost[t] * model.backlog[t]
            for t in model.T
        ),
        sense=pyo.minimize,
    )

    # APPsi may raise RuntimeError when it cannot load a feasible solution.
    # Objective retrieval alone determines whether this function reports success.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}