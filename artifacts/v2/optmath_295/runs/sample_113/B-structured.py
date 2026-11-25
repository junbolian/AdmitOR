# IR: {"sets":{"I":"0..46"},"params":{"profit_margin":"real[I], from params","resource_usage":"real[I], from params","capacity":"real[I], from params","resource_limit":"real, from params"},"variables":{"quantity":"nonnegative continuous[I]"},"constraints":["sum(resource_usage[i]*quantity[i] for i in I) <= resource_limit","quantity[i] <= capacity[i] for each i in I"],"objective":{"sense":"maximize","expression":"sum(profit_margin[i]*quantity[i] for i in I)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.item_set = pyo.RangeSet(0, 46)

    model.profit_margin = pyo.Param(
        model.item_set,
        initialize={i: params["profit_margin"][i] for i in model.item_set},
        within=pyo.Reals,
    )
    model.resource_usage = pyo.Param(
        model.item_set,
        initialize={i: params["resource_usage"][i] for i in model.item_set},
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.item_set,
        initialize={i: params["capacity"][i] for i in model.item_set},
        within=pyo.Reals,
    )
    model.resource_limit = pyo.Param(
        initialize=params["resource_limit"],
        within=pyo.Reals,
    )

    model.quantity = pyo.Var(
        model.item_set,
        domain=pyo.NonNegativeReals,
    )

    model.resource_constraint = pyo.Constraint(
        expr=sum(
            model.resource_usage[i] * model.quantity[i]
            for i in model.item_set
        ) <= model.resource_limit
    )

    def capacity_rule(instance, i):
        return instance.quantity[i] <= instance.capacity[i]

    model.capacity_constraints = pyo.Constraint(
        model.item_set,
        rule=capacity_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_margin[i] * model.quantity[i]
            for i in model.item_set
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}