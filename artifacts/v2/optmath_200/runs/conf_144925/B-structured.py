# IR: {"sets":{"T":[1,2,3,4,5],"S":[0,1,2,3,4,5]},"params":{"fixed_setup_cost":"T-indexed","variable_production_cost":"T-indexed","inventory_holding_cost":"T-indexed","backlog_penalty":"T-indexed","production_capacity":"scalar","demand":"T-indexed"},"variables":{"production[T]":"nonnegative continuous","inventory[S]":"nonnegative continuous","backlog[S]":"nonnegative continuous","setup[T]":"binary"},"constraints":["production[t]+inventory[t-1]-backlog[t-1]=demand[t]+inventory[t]-backlog[t] for t in T","production[t]<=production_capacity*setup[t] for t in T","inventory[0]=inventory[5]=0","backlog[0]=backlog[5]=0"],"objective":"minimize sum(fixed_setup_cost[t]*setup[t]+variable_production_cost[t]*production[t]+inventory_holding_cost[t]*inventory[t]+backlog_penalty[t]*backlog[t] for t in T)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept period data as length-five sequences or mappings keyed 1 through 5."""

    def period_value(values, period):
        if isinstance(values, Mapping):
            return values[period]
        return values[period - 1]

    model = pyo.ConcreteModel()
    model.T = pyo.RangeSet(1, 5)
    model.S = pyo.RangeSet(0, 5)

    model.fixed_setup_cost = pyo.Param(
        model.T,
        initialize=lambda _, period: period_value(
            params["fixed_setup_cost"], period
        ),
    )
    model.variable_production_cost = pyo.Param(
        model.T,
        initialize=lambda _, period: period_value(
            params["variable_production_cost"], period
        ),
    )
    model.inventory_holding_cost = pyo.Param(
        model.T,
        initialize=lambda _, period: period_value(
            params["inventory_holding_cost"], period
        ),
    )
    model.backlog_penalty = pyo.Param(
        model.T,
        initialize=lambda _, period: period_value(
            params["backlog_penalty"], period
        ),
    )
    model.production_capacity = pyo.Param(
        initialize=params["production_capacity"],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.T,
        initialize=lambda _, period: period_value(params["demand"], period),
        within=pyo.NonNegativeReals,
    )

    model.production = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.S, domain=pyo.NonNegativeReals)
    model.backlog = pyo.Var(model.S, domain=pyo.NonNegativeReals)
    model.setup = pyo.Var(model.T, domain=pyo.Binary)

    model.inventory[0].fix(0)
    model.inventory[5].fix(0)
    model.backlog[0].fix(0)
    model.backlog[5].fix(0)

    def balance_rule(_, period):
        return (
            model.production[period]
            + model.inventory[period - 1]
            - model.backlog[period - 1]
            == model.demand[period]
            + model.inventory[period]
            - model.backlog[period]
        )

    model.flow_balance = pyo.Constraint(model.T, rule=balance_rule)

    model.capacity_limit = pyo.Constraint(
        model.T,
        rule=lambda _, period: (
            model.production[period]
            <= model.production_capacity * model.setup[period]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_setup_cost[period] * model.setup[period]
            + model.variable_production_cost[period] * model.production[period]
            + model.inventory_holding_cost[period] * model.inventory[period]
            + model.backlog_penalty[period] * model.backlog[period]
            for period in model.T
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