# IR: {"sets":{"T":"1..14","T0":"0..14"},"params":{"fixed_ordering_cost":"real[T]","variable_ordering_cost":"real[T]","inventory_holding_cost":"real[T]","demand":"nonnegative_real[T]","max_order_quantity":"nonnegative_real","initial_inventory":"nonnegative_real, required zero","final_inventory":"nonnegative_real, required zero"},"variables":{"order_placed[T]":"binary","order_quantity[T]":"nonnegative_real","inventory[T0]":"nonnegative_real"},"constraints":["inventory[t-1]+order_quantity[t]=demand[t]+inventory[t] for t in T","order_quantity[t]<=max_order_quantity*order_placed[t] for t in T","inventory[0]=initial_inventory","inventory[14]=final_inventory","inventory[0]=0","inventory[14]=0"],"objective":"minimize sum(fixed_ordering_cost[t]*order_placed[t]+variable_ordering_cost[t]*order_quantity[t]+inventory_holding_cost[t]*inventory[t] for t in T)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the 14-period inventory problem.

    Period parameters accept sequences of length 14, ordered by period,
    or mappings keyed by periods 1 through 14 (integer or string keys).
    """

    def period_data(values):
        if isinstance(values, Mapping):
            return {
                period: values[period] if period in values else values[str(period)]
                for period in range(1, 15)
            }
        if len(values) != 14:
            raise ValueError("Each period parameter must contain 14 values.")
        return {period: values[period - 1] for period in range(1, 15)}

    model = pyo.ConcreteModel()
    model.periods = pyo.RangeSet(1, 14)
    model.inventory_periods = pyo.RangeSet(0, 14)

    model.fixed_ordering_cost = pyo.Param(
        model.periods,
        initialize=period_data(params["fixed_ordering_cost"]),
        within=pyo.Reals,
    )
    model.variable_ordering_cost = pyo.Param(
        model.periods,
        initialize=period_data(params["variable_ordering_cost"]),
        within=pyo.Reals,
    )
    model.inventory_holding_cost = pyo.Param(
        model.periods,
        initialize=period_data(params["inventory_holding_cost"]),
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.periods,
        initialize=period_data(params["demand"]),
        within=pyo.NonNegativeReals,
    )
    model.max_order_quantity = pyo.Param(
        initialize=params["max_order_quantity"],
        within=pyo.NonNegativeReals,
    )
    model.initial_inventory = pyo.Param(
        initialize=params["initial_inventory"],
        within=pyo.NonNegativeReals,
    )
    model.final_inventory = pyo.Param(
        initialize=params["final_inventory"],
        within=pyo.NonNegativeReals,
    )

    model.order_placed = pyo.Var(model.periods, domain=pyo.Binary)
    model.order_quantity = pyo.Var(model.periods, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(
        model.inventory_periods, domain=pyo.NonNegativeReals
    )

    def inventory_balance_rule(instance, period):
        return (
            instance.inventory[period - 1] + instance.order_quantity[period]
            == instance.demand[period] + instance.inventory[period]
        )

    model.inventory_balance = pyo.Constraint(
        model.periods, rule=inventory_balance_rule
    )

    def order_limit_rule(instance, period):
        return (
            instance.order_quantity[period]
            <= instance.max_order_quantity * instance.order_placed[period]
        )

    model.order_limit = pyo.Constraint(
        model.periods, rule=order_limit_rule
    )
    model.initial_inventory_requirement = pyo.Constraint(
        expr=model.inventory[0] == model.initial_inventory
    )
    model.final_inventory_requirement = pyo.Constraint(
        expr=model.inventory[14] == model.final_inventory
    )
    model.zero_initial_inventory = pyo.Constraint(
        expr=model.inventory[0] == 0
    )
    model.zero_final_inventory = pyo.Constraint(
        expr=model.inventory[14] == 0
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_ordering_cost[period] * model.order_placed[period]
            + model.variable_ordering_cost[period] * model.order_quantity[period]
            + model.inventory_holding_cost[period] * model.inventory[period]
            for period in model.periods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}