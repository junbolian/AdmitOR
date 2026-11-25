# IR: {"sets":{"T":[1,2,3,4,5,6],"S":[0,1,2,3,4,5,6]},"params":{"fixed_setup_cost":"T-indexed","variable_production_cost":"T-indexed","inventory_holding_cost":"T-indexed","backlogging_cost":"T-indexed","demand":"T-indexed","production_capacity":"scalar"},"variables":{"setup[T]":"Binary","production[T]":"NonNegativeReals","inventory[S]":"NonNegativeReals","backlog[S]":"NonNegativeReals"},"constraints":["inventory[t-1]-backlog[t-1]+production[t]=demand[t]+inventory[t]-backlog[t] for t in T","production[t]<=production_capacity*setup[t] for t in T","inventory[0]=inventory[6]=0","backlog[0]=backlog[6]=0"],"objective":"min sum(t in T: fixed_setup_cost[t]*setup[t]+variable_production_cost[t]*production[t]+inventory_holding_cost[t]*inventory[t]+backlogging_cost[t]*backlog[t])"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Period inputs accept six-item sequences or mappings keyed by 1..6."""

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

    model.fixed_setup_cost = pyo.Param(
        model.T, initialize=period_values(params["fixed_setup_cost"])
    )
    model.variable_production_cost = pyo.Param(
        model.T, initialize=period_values(params["variable_production_cost"])
    )
    model.inventory_holding_cost = pyo.Param(
        model.T, initialize=period_values(params["inventory_holding_cost"])
    )
    model.backlogging_cost = pyo.Param(
        model.T, initialize=period_values(params["backlogging_cost"])
    )
    model.demand = pyo.Param(
        model.T, initialize=period_values(params["demand"])
    )
    model.production_capacity = pyo.Param(
        initialize=params["production_capacity"]
    )

    model.setup = pyo.Var(model.T, domain=pyo.Binary)
    model.production = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.S, domain=pyo.NonNegativeReals)
    model.backlog = pyo.Var(model.S, domain=pyo.NonNegativeReals)

    model.inventory[0].fix(0)
    model.inventory[6].fix(0)
    model.backlog[0].fix(0)
    model.backlog[6].fix(0)

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

    def capacity_rule(instance, period):
        return (
            instance.production[period]
            <= instance.production_capacity * instance.setup[period]
        )

    model.capacity_limit = pyo.Constraint(model.T, rule=capacity_rule)

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
    except RuntimeError as exc:
        # APPsi raises this error when it cannot load a feasible solution.
        # Leave unexpected solver errors visible to the calling harness.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}