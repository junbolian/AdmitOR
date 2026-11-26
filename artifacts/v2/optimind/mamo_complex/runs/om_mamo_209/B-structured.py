# IR: {"sets":{"Q":[1,2,3,4]},"params":{"demand":"params['demand']: sequence of four quarterly demands","initial_inventory":"params['initial_inventory']","regular_capacity":"params['regular_capacity']","regular_cost":"params['regular_cost']","overtime_cost":"params['overtime_cost']","holding_cost":"params['holding_cost']"},"variables":{"regular[q]":"nonnegative continuous","overtime[q]":"nonnegative continuous","inventory[q]":"nonnegative continuous"},"constraints":["regular[q] <= regular_capacity for q in Q","inventory[q] = (initial_inventory if q == 1 else inventory[q-1]) + regular[q] + overtime[q] - demand[q] for q in Q"],"objective":"minimize sum(regular_cost*regular[q] + overtime_cost*overtime[q] + holding_cost*inventory[q] for q in Q)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the four-quarter LP; demand is a four-element sequence."""
    model = pyo.ConcreteModel()
    model.quarters = pyo.RangeSet(1, 4)

    model.demand = pyo.Param(
        model.quarters,
        initialize={
            quarter: params["demand"][quarter - 1]
            for quarter in model.quarters
        },
    )
    model.initial_inventory = pyo.Param(
        initialize=params["initial_inventory"]
    )
    model.regular_capacity = pyo.Param(
        initialize=params["regular_capacity"]
    )
    model.regular_cost = pyo.Param(initialize=params["regular_cost"])
    model.overtime_cost = pyo.Param(initialize=params["overtime_cost"])
    model.holding_cost = pyo.Param(initialize=params["holding_cost"])

    model.regular = pyo.Var(
        model.quarters, domain=pyo.NonNegativeReals
    )
    model.overtime = pyo.Var(
        model.quarters, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.quarters, domain=pyo.NonNegativeReals
    )

    def capacity_rule(model, quarter):
        return model.regular[quarter] <= model.regular_capacity

    model.capacity_limits = pyo.Constraint(
        model.quarters, rule=capacity_rule
    )

    def inventory_rule(model, quarter):
        beginning_inventory = (
            model.initial_inventory
            if quarter == 1
            else model.inventory[quarter - 1]
        )
        return model.inventory[quarter] == (
            beginning_inventory
            + model.regular[quarter]
            + model.overtime[quarter]
            - model.demand[quarter]
        )

    model.inventory_balances = pyo.Constraint(
        model.quarters, rule=inventory_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.regular_cost * model.regular[quarter]
            + model.overtime_cost * model.overtime[quarter]
            + model.holding_cost * model.inventory[quarter]
            for quarter in model.quarters
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