# IR: {"sets":{"item_index":"0..14"},"params":{"profit":"real[item_index]","resource_consumption":"real[item_index]","resource_capacity":"real","production_limits":"real[item_index]"},"variables":{"quantity":"nonnegative continuous[item_index]"},"constraints":["sum(resource_consumption[i]*quantity[i] for i in item_index) <= resource_capacity","quantity[i] <= production_limits[i] for each i in item_index"],"objective":"maximize sum(profit[i]*quantity[i] for i in item_index)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.item_index = pyo.RangeSet(0, 14)

    model.profit = pyo.Param(
        model.item_index,
        initialize={i: params["profit"][i] for i in model.item_index},
        within=pyo.Reals,
    )
    model.resource_consumption = pyo.Param(
        model.item_index,
        initialize={
            i: params["resource_consumption"][i] for i in model.item_index
        },
        within=pyo.Reals,
    )
    model.resource_capacity = pyo.Param(
        initialize=params["resource_capacity"],
        within=pyo.Reals,
    )
    model.production_limits = pyo.Param(
        model.item_index,
        initialize={
            i: params["production_limits"][i] for i in model.item_index
        },
        within=pyo.Reals,
    )

    model.quantity = pyo.Var(
        model.item_index,
        domain=pyo.NonNegativeReals,
    )

    model.resource_constraint = pyo.Constraint(
        expr=sum(
            model.resource_consumption[i] * model.quantity[i]
            for i in model.item_index
        )
        <= model.resource_capacity
    )

    def production_limit_rule(instance, i):
        return instance.quantity[i] <= instance.production_limits[i]

    model.production_limit_constraints = pyo.Constraint(
        model.item_index,
        rule=production_limit_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[i] * model.quantity[i]
            for i in model.item_index
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}