# IR: {"sets":{"T":"1..25","S":"0..25"},"params":{"fixed_ordering_cost":"weekly, indexed by T","unit_purchase_cost":"weekly, indexed by T","holding_cost":"weekly, indexed by T","demand":"weekly, indexed by T","order_limit":"scalar"},"variables":{"order_placed[t]":"binary, t in T","order_quantity[t]":"continuous nonnegative, t in T","inventory[s]":"continuous nonnegative, s in S"},"constraints":["inventory[0] = 0","inventory[25] = 0","inventory[t-1] + order_quantity[t] = demand[t] + inventory[t], t in T","order_quantity[t] <= order_limit * order_placed[t], t in T"],"objective":"minimize sum(t in T: fixed_ordering_cost[t]*order_placed[t] + unit_purchase_cost[t]*order_quantity[t] + holding_cost[t]*inventory[t])"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using weekly sequences or mappings keyed by week (1 through 25)."""

    def weekly_values(values):
        if isinstance(values, Mapping):
            return {
                week: values[week] if week in values else values[str(week)]
                for week in range(1, 26)
            }
        return {week: values[week - 1] for week in range(1, 26)}

    fixed_cost = weekly_values(params["fixed_ordering_cost"])
    purchase_cost = weekly_values(params["unit_purchase_cost"])
    holding_cost = weekly_values(params["holding_cost"])
    demand = weekly_values(params["demand"])
    order_limit = params["order_limit"]

    model = pyo.ConcreteModel()
    model.weeks = pyo.RangeSet(1, 25)
    model.inventory_periods = pyo.RangeSet(0, 25)

    model.fixed_ordering_cost = pyo.Param(model.weeks, initialize=fixed_cost)
    model.unit_purchase_cost = pyo.Param(model.weeks, initialize=purchase_cost)
    model.holding_cost = pyo.Param(model.weeks, initialize=holding_cost)
    model.demand = pyo.Param(model.weeks, initialize=demand)
    model.order_limit = pyo.Param(initialize=order_limit)

    model.order_placed = pyo.Var(model.weeks, domain=pyo.Binary)
    model.order_quantity = pyo.Var(model.weeks, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(
        model.inventory_periods, domain=pyo.NonNegativeReals
    )

    model.starting_inventory = pyo.Constraint(expr=model.inventory[0] == 0)
    model.ending_inventory = pyo.Constraint(expr=model.inventory[25] == 0)

    def inventory_balance_rule(instance, week):
        return (
            instance.inventory[week - 1] + instance.order_quantity[week]
            == instance.demand[week] + instance.inventory[week]
        )

    model.inventory_balance = pyo.Constraint(
        model.weeks, rule=inventory_balance_rule
    )

    def order_capacity_rule(instance, week):
        return (
            instance.order_quantity[week]
            <= instance.order_limit * instance.order_placed[week]
        )

    model.order_capacity = pyo.Constraint(
        model.weeks, rule=order_capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_ordering_cost[week] * model.order_placed[week]
            + model.unit_purchase_cost[week] * model.order_quantity[week]
            + model.holding_cost[week] * model.inventory[week]
            for week in model.weeks
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}