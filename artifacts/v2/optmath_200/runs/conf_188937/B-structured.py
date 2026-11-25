# IR: {"sets":{"T":"1..period_count","T0":"0..period_count"},"params":{"production_cost":"vector on T","holding_cost":"vector on T","backlog_cost":"vector on T","setup_cost":"vector on T","production_capacity":"scalar","demand":"vector on T","period_count":"positive integer"},"variables":{"production[t]":"nonnegative continuous, t in T","inventory[t]":"nonnegative continuous, t in T0","backlog[t]":"nonnegative continuous, t in T0","setup[t]":"binary, t in T"},"constraints":["production[t] <= production_capacity * setup[t] for t in T","inventory[t] - backlog[t] = inventory[t-1] - backlog[t-1] + production[t] - demand[t] for t in T","inventory[0] = inventory[period_count] = 0","backlog[0] = backlog[period_count] = 0"],"objective":"minimize sum(production_cost[t]*production[t] + holding_cost[t]*inventory[t] + backlog_cost[t]*backlog[t] + setup_cost[t]*setup[t] for t in T)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    period_count = int(params["period_count"])
    if period_count <= 0:
        raise ValueError("period_count must be positive.")

    def period_data(values):
        """Accept a sequence or a dictionary keyed by one-based periods."""
        if isinstance(values, Mapping):
            return {
                t: values[t] if t in values else values[str(t)]
                for t in range(1, period_count + 1)
            }
        if len(values) != period_count:
            raise ValueError("Period data must have period_count entries.")
        return {t: values[t - 1] for t in range(1, period_count + 1)}

    production_cost = period_data(params["production_cost"])
    holding_cost = period_data(params["holding_cost"])
    backlog_cost = period_data(params["backlog_cost"])
    setup_cost = period_data(params["setup_cost"])
    production_capacity = params["production_capacity"]
    demand = period_data(params["demand"])

    model = pyo.ConcreteModel()
    model.T = pyo.RangeSet(1, period_count)
    model.T0 = pyo.RangeSet(0, period_count)

    model.production_cost = pyo.Param(model.T, initialize=production_cost)
    model.holding_cost = pyo.Param(model.T, initialize=holding_cost)
    model.backlog_cost = pyo.Param(model.T, initialize=backlog_cost)
    model.setup_cost = pyo.Param(model.T, initialize=setup_cost)
    model.production_capacity = pyo.Param(initialize=production_capacity)
    model.demand = pyo.Param(model.T, initialize=demand)

    model.production = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.T0, domain=pyo.NonNegativeReals)
    model.backlog = pyo.Var(model.T0, domain=pyo.NonNegativeReals)
    model.setup = pyo.Var(model.T, domain=pyo.Binary)

    model.inventory[0].fix(0)
    model.inventory[period_count].fix(0)
    model.backlog[0].fix(0)
    model.backlog[period_count].fix(0)

    def capacity_rule(mod, t):
        return mod.production[t] <= mod.production_capacity * mod.setup[t]

    model.capacity_limit = pyo.Constraint(model.T, rule=capacity_rule)

    def balance_rule(mod, t):
        return (
            mod.inventory[t] - mod.backlog[t]
            == mod.inventory[t - 1] - mod.backlog[t - 1]
            + mod.production[t] - mod.demand[t]
        )

    model.flow_balance = pyo.Constraint(model.T, rule=balance_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.production_cost[t] * model.production[t]
            + model.holding_cost[t] * model.inventory[t]
            + model.backlog_cost[t] * model.backlog[t]
            + model.setup_cost[t] * model.setup[t]
            for t in model.T
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