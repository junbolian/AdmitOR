# IR: {"sets":{"T":"1..14","T_inventory":"0..14"},"params":{"fixed_ordering_costs":"real[T]","variable_ordering_costs":"real[T]","inventory_holding_costs":"real[T]","demand":"nonnegative_real[T]","order_capacity":"nonnegative_real","initial_inventory":"nonnegative_real","final_inventory":"nonnegative_real"},"variables":{"order_placed":"binary[T]","order_quantity":"nonnegative_continuous[T]","inventory":"nonnegative_continuous[T_inventory]"},"constraints":["inventory[0] = initial_inventory","inventory[t-1] + order_quantity[t] = demand[t] + inventory[t] for t in T","order_quantity[t] <= order_capacity * order_placed[t] for t in T","inventory[14] = final_inventory"],"objective":"minimize sum(fixed_ordering_costs[t]*order_placed[t] + variable_ordering_costs[t]*order_quantity[t] + inventory_holding_costs[t]*inventory[t] for t in T)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Period-dependent inputs accept sequences of length 14 or mappings
    keyed by periods 1 through 14 (integer keys or string keys).
    """

    def period_values(values):
        if isinstance(values, Mapping):
            return {
                t: values[t] if t in values else values[str(t)]
                for t in range(1, 15)
            }
        if len(values) != 14:
            raise ValueError("Period-dependent inputs must contain 14 values.")
        return {t: values[t - 1] for t in range(1, 15)}

    model = pyo.ConcreteModel()
    model.periods = pyo.RangeSet(1, 14)
    model.inventory_periods = pyo.RangeSet(0, 14)

    model.fixed_ordering_costs = pyo.Param(
        model.periods,
        initialize=period_values(params["fixed_ordering_costs"]),
        within=pyo.Reals,
    )
    model.variable_ordering_costs = pyo.Param(
        model.periods,
        initialize=period_values(params["variable_ordering_costs"]),
        within=pyo.Reals,
    )
    model.inventory_holding_costs = pyo.Param(
        model.periods,
        initialize=period_values(params["inventory_holding_costs"]),
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.periods,
        initialize=period_values(params["demand"]),
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

    model.initial_inventory_requirement = pyo.Constraint(
        expr=model.inventory[0] == model.initial_inventory
    )

    def inventory_balance_rule(mdl, t):
        return (
            mdl.inventory[t - 1] + mdl.order_quantity[t]
            == mdl.demand[t] + mdl.inventory[t]
        )

    model.inventory_balance = pyo.Constraint(
        model.periods, rule=inventory_balance_rule
    )

    def order_capacity_rule(mdl, t):
        return (
            mdl.order_quantity[t]
            <= mdl.order_capacity * mdl.order_placed[t]
        )

    model.order_capacity_limit = pyo.Constraint(
        model.periods, rule=order_capacity_rule
    )
    model.final_inventory_requirement = pyo.Constraint(
        expr=model.inventory[14] == model.final_inventory
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_ordering_costs[t] * model.order_placed[t]
            + model.variable_ordering_costs[t] * model.order_quantity[t]
            + model.inventory_holding_costs[t] * model.inventory[t]
            for t in model.periods
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