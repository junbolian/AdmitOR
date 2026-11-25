# IR: {"sets":{"T":[1,2,3,4,5,6],"S":[0,1,2,3,4,5,6],"E":[0,6]},"params":{"fixed_setup_cost":"T -> real","variable_production_cost":"T -> real","inventory_holding_cost":"T -> real","backlogging_cost":"T -> real","demand":"T -> nonnegative real","production_capacity":"nonnegative real"},"variables":{"setup[t in T]":"binary","production[t in T]":"nonnegative continuous","inventory[t in S]":"nonnegative continuous","backlog[t in S]":"nonnegative continuous"},"constraints":["inventory[t-1]-backlog[t-1]+production[t]=demand[t]+inventory[t]-backlog[t] for t in T","production[t]<=production_capacity*setup[t] for t in T","inventory[t]=0 for t in E","backlog[t]=0 for t in E"],"objective":"minimize sum(fixed_setup_cost[t]*setup[t]+variable_production_cost[t]*production[t]+inventory_holding_cost[t]*inventory[t]+backlogging_cost[t]*backlog[t] for t in T)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Period parameters accept six-element sequences in chronological order,
    or mappings keyed by periods 1 through 6 (integers or strings).
    production_capacity is a scalar.
    """

    def period_values(values):
        if isinstance(values, Mapping):
            return {
                period: values[period] if period in values else values[str(period)]
                for period in range(1, 7)
            }
        return {period: values[period - 1] for period in range(1, 7)}

    model = pyo.ConcreteModel()

    model.T = pyo.RangeSet(1, 6)
    model.S = pyo.RangeSet(0, 6)
    model.E = pyo.Set(initialize=[0, 6])

    model.fixed_setup_cost = pyo.Param(
        model.T,
        initialize=period_values(params["fixed_setup_cost"]),
        within=pyo.Reals,
    )
    model.variable_production_cost = pyo.Param(
        model.T,
        initialize=period_values(params["variable_production_cost"]),
        within=pyo.Reals,
    )
    model.inventory_holding_cost = pyo.Param(
        model.T,
        initialize=period_values(params["inventory_holding_cost"]),
        within=pyo.Reals,
    )
    model.backlogging_cost = pyo.Param(
        model.T,
        initialize=period_values(params["backlogging_cost"]),
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.T,
        initialize=period_values(params["demand"]),
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

    def balance_rule(instance, period):
        return (
            instance.inventory[period - 1]
            - instance.backlog[period - 1]
            + instance.production[period]
            == instance.demand[period]
            + instance.inventory[period]
            - instance.backlog[period]
        )

    model.demand_balance = pyo.Constraint(model.T, rule=balance_rule)

    model.capacity_limit = pyo.Constraint(
        model.T,
        rule=lambda instance, period: (
            instance.production[period]
            <= instance.production_capacity * instance.setup[period]
        ),
    )

    model.inventory_boundary = pyo.Constraint(
        model.E,
        rule=lambda instance, period: instance.inventory[period] == 0,
    )
    model.backlog_boundary = pyo.Constraint(
        model.E,
        rule=lambda instance, period: instance.backlog[period] == 0,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_setup_cost[period] * model.setup[period]
            + model.variable_production_cost[period] * model.production[period]
            + model.inventory_holding_cost[period] * model.inventory[period]
            + model.backlogging_cost[period] * model.backlog[period]
            for period in model.T
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}