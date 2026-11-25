# IR: {"sets":{"T":[1,2,3,4,5],"T0":[0,1,2,3,4,5]},"params":{"demand":"T -> units","production_cost":"T -> $/unit","inventory_cost":"T -> $/unit","backlog_cost":"T -> $/unit","setup_cost":"T -> $","production_capacity":"scalar units"},"variables":{"OrderedAmount":"T -> nonnegative real","EndingInventory":"T0 -> nonnegative real","BackloggedAmount":"T0 -> nonnegative real","OrderIsPlaced":"T -> binary"},"constraints":["EndingInventory[0] = BackloggedAmount[0] = 0","EndingInventory[5] = BackloggedAmount[5] = 0","OrderedAmount[t] + EndingInventory[t-1] - BackloggedAmount[t-1] = demand[t] + EndingInventory[t] - BackloggedAmount[t], t in T","OrderedAmount[t] <= production_capacity * OrderIsPlaced[t], t in T"],"objective":"min sum(t in T: production_cost[t]*OrderedAmount[t] + inventory_cost[t]*EndingInventory[t] + backlog_cost[t]*BackloggedAmount[t] + setup_cost[t]*OrderIsPlaced[t])"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Monthly inputs may be five-element sequences or month-keyed mappings."""

    def monthly_values(values):
        if isinstance(values, Mapping):
            return {
                month: values[month] if month in values else values[str(month)]
                for month in range(1, 6)
            }
        return {month: values[month - 1] for month in range(1, 6)}

    demand = monthly_values(params["demand"])
    production_cost = monthly_values(params["production_cost"])
    inventory_cost = monthly_values(params["inventory_cost"])
    backlog_cost = monthly_values(params["backlog_cost"])
    setup_cost = monthly_values(params["setup_cost"])
    production_capacity = params["production_capacity"]

    model = pyo.ConcreteModel()
    model.months = pyo.RangeSet(1, 5)
    model.inventory_periods = pyo.RangeSet(0, 5)

    model.demand = pyo.Param(model.months, initialize=demand)
    model.production_cost = pyo.Param(model.months, initialize=production_cost)
    model.inventory_cost = pyo.Param(model.months, initialize=inventory_cost)
    model.backlog_cost = pyo.Param(model.months, initialize=backlog_cost)
    model.setup_cost = pyo.Param(model.months, initialize=setup_cost)
    model.production_capacity = pyo.Param(initialize=production_capacity)

    model.OrderedAmount = pyo.Var(model.months, domain=pyo.NonNegativeReals)
    model.EndingInventory = pyo.Var(
        model.inventory_periods, domain=pyo.NonNegativeReals
    )
    model.BackloggedAmount = pyo.Var(
        model.inventory_periods, domain=pyo.NonNegativeReals
    )
    model.OrderIsPlaced = pyo.Var(model.months, domain=pyo.Binary)

    model.EndingInventory[0].fix(0)
    model.BackloggedAmount[0].fix(0)
    model.EndingInventory[5].fix(0)
    model.BackloggedAmount[5].fix(0)

    def balance_rule(mdl, month):
        return (
            mdl.OrderedAmount[month]
            + mdl.EndingInventory[month - 1]
            - mdl.BackloggedAmount[month - 1]
            == mdl.demand[month]
            + mdl.EndingInventory[month]
            - mdl.BackloggedAmount[month]
        )

    model.flow_balance = pyo.Constraint(model.months, rule=balance_rule)

    def capacity_rule(mdl, month):
        return (
            mdl.OrderedAmount[month]
            <= mdl.production_capacity * mdl.OrderIsPlaced[month]
        )

    model.production_limit = pyo.Constraint(model.months, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.production_cost[month] * model.OrderedAmount[month]
            + model.inventory_cost[month] * model.EndingInventory[month]
            + model.backlog_cost[month] * model.BackloggedAmount[month]
            + model.setup_cost[month] * model.OrderIsPlaced[month]
            for month in model.months
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when no feasible solution can be loaded.
        if "feasible solution" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}