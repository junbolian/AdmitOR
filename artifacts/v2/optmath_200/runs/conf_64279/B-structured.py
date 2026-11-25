# IR: {"sets":{"T":[1,2,3,4,5,6]},"params":{"production_cost":"by month","fixed_order_cost":"by month","holding_cost":"by month","backlog_cost":"by month","demand":"by month","production_capacity":"scalar"},"variables":{"produce[t]":"nonnegative continuous","order[t]":"binary","inventory[t]":"nonnegative continuous","backlog[t]":"nonnegative continuous"},"constraints":["produce[t] <= production_capacity * order[t] for t in T","inventory[t] - backlog[t] = previous_inventory - previous_backlog + produce[t] - demand[t], with initial inventory and backlog zero","inventory[6] = 0","backlog[6] = 0"],"objective":"minimize sum_t(production_cost[t]*produce[t] + fixed_order_cost[t]*order[t] + holding_cost[t]*inventory[t] + backlog_cost[t]*backlog[t])"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Monthly inputs may be six-element sequences or mappings keyed 1..6."""

    def monthly_values(values):
        if isinstance(values, Mapping):
            return {
                month: values[month] if month in values else values[str(month)]
                for month in range(1, 7)
            }
        return {month: values[month - 1] for month in range(1, 7)}

    model = pyo.ConcreteModel()
    model.months = pyo.RangeSet(1, 6)

    model.production_cost = pyo.Param(
        model.months, initialize=monthly_values(params["production_cost"])
    )
    model.fixed_order_cost = pyo.Param(
        model.months, initialize=monthly_values(params["fixed_order_cost"])
    )
    model.holding_cost = pyo.Param(
        model.months, initialize=monthly_values(params["holding_cost"])
    )
    model.backlog_cost = pyo.Param(
        model.months, initialize=monthly_values(params["backlog_cost"])
    )
    model.demand = pyo.Param(
        model.months, initialize=monthly_values(params["demand"])
    )
    model.production_capacity = pyo.Param(
        initialize=params["production_capacity"]
    )

    model.produce = pyo.Var(model.months, domain=pyo.NonNegativeReals)
    model.order = pyo.Var(model.months, domain=pyo.Binary)
    model.inventory = pyo.Var(model.months, domain=pyo.NonNegativeReals)
    model.backlog = pyo.Var(model.months, domain=pyo.NonNegativeReals)

    def capacity_rule(model, month):
        return (
            model.produce[month]
            <= model.production_capacity * model.order[month]
        )

    model.capacity_limit = pyo.Constraint(model.months, rule=capacity_rule)

    def balance_rule(model, month):
        previous_net_inventory = (
            0
            if month == 1
            else model.inventory[month - 1] - model.backlog[month - 1]
        )
        return (
            model.inventory[month] - model.backlog[month]
            == previous_net_inventory + model.produce[month] - model.demand[month]
        )

    model.inventory_balance = pyo.Constraint(model.months, rule=balance_rule)
    model.final_inventory = pyo.Constraint(expr=model.inventory[6] == 0)
    model.final_backlog = pyo.Constraint(expr=model.backlog[6] == 0)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.production_cost[month] * model.produce[month]
            + model.fixed_order_cost[month] * model.order[month]
            + model.holding_cost[month] * model.inventory[month]
            + model.backlog_cost[month] * model.backlog[month]
            for month in model.months
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