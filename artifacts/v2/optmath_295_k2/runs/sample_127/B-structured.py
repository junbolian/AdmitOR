# IR: {"sets":{"T":"1..14","T0":"0..14"},"params":{"fixed_ordering_costs":"T-indexed","variable_ordering_costs":"T-indexed","inventory_holding_costs":"T-indexed","demand":"T-indexed","order_capacity":"scalar","initial_inventory":"scalar","final_inventory":"scalar"},"variables":{"order_placed[t]":"binary, t in T","order_quantity[t]":"continuous >= 0, t in T","inventory[t]":"continuous >= 0, t in T0"},"constraints":["inventory[0] = initial_inventory","inventory[t-1] + order_quantity[t] = demand[t] + inventory[t], t in T","order_quantity[t] <= order_capacity * order_placed[t], t in T","inventory[14] = final_inventory"],"objective":"min sum(t in T: fixed_ordering_costs[t]*order_placed[t] + variable_ordering_costs[t]*order_quantity[t] + inventory_holding_costs[t]*inventory[t])"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Solve the 14-period inventory and ordering problem.

    Period-specific inputs may be sequences of length 14, ordered from
    period 1 through period 14, or mappings keyed by integers 1 through 14.
    """
    periods = range(1, 15)

    def period_data(values):
        if isinstance(values, Mapping):
            return {period: values[period] for period in periods}
        if len(values) != len(periods):
            raise ValueError("Period-specific sequences must have length 14.")
        return {period: values[period - 1] for period in periods}

    model = pyo.ConcreteModel()
    model.periods = pyo.RangeSet(1, 14)
    model.inventory_periods = pyo.RangeSet(0, 14)

    model.fixed_ordering_costs = pyo.Param(
        model.periods,
        initialize=period_data(params["fixed_ordering_costs"]),
        within=pyo.Reals,
    )
    model.variable_ordering_costs = pyo.Param(
        model.periods,
        initialize=period_data(params["variable_ordering_costs"]),
        within=pyo.Reals,
    )
    model.inventory_holding_costs = pyo.Param(
        model.periods,
        initialize=period_data(params["inventory_holding_costs"]),
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.periods,
        initialize=period_data(params["demand"]),
        within=pyo.NonNegativeReals,
    )
    model.order_capacity = pyo.Param(
        initialize=params["order_capacity"],
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
    model.order_quantity = pyo.Var(
        model.periods, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.inventory_periods, domain=pyo.NonNegativeReals
    )

    model.starting_inventory_constraint = pyo.Constraint(
        expr=model.inventory[0] == model.initial_inventory
    )

    def inventory_balance_rule(instance, period):
        return (
            instance.inventory[period - 1]
            + instance.order_quantity[period]
            == instance.demand[period] + instance.inventory[period]
        )

    model.inventory_balance_constraints = pyo.Constraint(
        model.periods, rule=inventory_balance_rule
    )

    def order_capacity_rule(instance, period):
        return (
            instance.order_quantity[period]
            <= instance.order_capacity * instance.order_placed[period]
        )

    model.order_capacity_constraints = pyo.Constraint(
        model.periods, rule=order_capacity_rule
    )

    model.ending_inventory_constraint = pyo.Constraint(
        expr=model.inventory[14] == model.final_inventory
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_ordering_costs[period] * model.order_placed[period]
            + model.variable_ordering_costs[period]
            * model.order_quantity[period]
            + model.inventory_holding_costs[period] * model.inventory[period]
            for period in model.periods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}