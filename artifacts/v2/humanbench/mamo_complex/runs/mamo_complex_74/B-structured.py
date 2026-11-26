# IR: {"sets":{"T":[1,2,3,4,5,6]},"params":{"demand":"params['demand']: six-element sequence ordered Jan-Jun","regular_capacity":"params['regular_capacity']","regular_cost":"params['regular_cost']","overtime_capacity":"params['overtime_capacity']","overtime_cost":"params['overtime_cost']","holding_cost":"params['holding_cost']","initial_inventory":"params['initial_inventory']"},"variables":{"regular[t]":"nonnegative integer","overtime[t]":"nonnegative integer","inventory[t]":"nonnegative integer, end-of-month stock"},"constraints":["regular[t] <= regular_capacity for t in T","overtime[t] <= overtime_capacity for t in T","inventory[t] = (initial_inventory if t=1 else inventory[t-1]) + regular[t] + overtime[t] - demand[t] for t in T"],"objective":"minimize sum(regular_cost*regular[t] + overtime_cost*overtime[t] + holding_cost*inventory[t] for t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Minimize six-month production and inventory costs."""
    model = pyo.ConcreteModel()
    model.months = pyo.RangeSet(1, 6)

    model.demand = pyo.Param(
        model.months,
        initialize={
            month: params["demand"][month - 1]
            for month in range(1, 7)
        },
        within=pyo.NonNegativeReals,
    )
    model.regular_capacity = pyo.Param(
        initialize=params["regular_capacity"],
        within=pyo.NonNegativeReals,
    )
    model.regular_cost = pyo.Param(
        initialize=params["regular_cost"],
        within=pyo.NonNegativeReals,
    )
    model.overtime_capacity = pyo.Param(
        initialize=params["overtime_capacity"],
        within=pyo.NonNegativeReals,
    )
    model.overtime_cost = pyo.Param(
        initialize=params["overtime_cost"],
        within=pyo.NonNegativeReals,
    )
    model.holding_cost = pyo.Param(
        initialize=params["holding_cost"],
        within=pyo.NonNegativeReals,
    )
    model.initial_inventory = pyo.Param(
        initialize=params["initial_inventory"],
        within=pyo.NonNegativeReals,
    )

    model.regular = pyo.Var(model.months, domain=pyo.NonNegativeIntegers)
    model.overtime = pyo.Var(model.months, domain=pyo.NonNegativeIntegers)
    model.inventory = pyo.Var(model.months, domain=pyo.NonNegativeIntegers)

    def regular_capacity_rule(model, month):
        return model.regular[month] <= model.regular_capacity

    model.regular_capacity_limit = pyo.Constraint(
        model.months, rule=regular_capacity_rule
    )

    def overtime_capacity_rule(model, month):
        return model.overtime[month] <= model.overtime_capacity

    model.overtime_capacity_limit = pyo.Constraint(
        model.months, rule=overtime_capacity_rule
    )

    def inventory_balance_rule(model, month):
        beginning_inventory = (
            model.initial_inventory
            if month == 1
            else model.inventory[month - 1]
        )
        return model.inventory[month] == (
            beginning_inventory
            + model.regular[month]
            + model.overtime[month]
            - model.demand[month]
        )

    model.inventory_balance = pyo.Constraint(
        model.months, rule=inventory_balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.regular_cost * model.regular[month]
            + model.overtime_cost * model.overtime[month]
            + model.holding_cost * model.inventory[month]
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
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}