# IR: {"sets":{"item_ids":"0..22"},"params":{"profit":"real[item_ids]","resource_consumption":"real[item_ids]","resource_capacity":"real","production_capacity":"real[item_ids]"},"variables":{"production":"nonnegative continuous[item_ids]"},"constraints":["sum(resource_consumption[i]*production[i] for i in item_ids) <= resource_capacity","production[i] <= production_capacity[i] for each i in item_ids"],"objective":"maximize sum(profit[i]*production[i] for i in item_ids)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.item_ids = pyo.RangeSet(0, 22)

    model.profit = pyo.Param(
        model.item_ids,
        initialize=lambda mdl, i: params["profit"][i],
        within=pyo.Reals,
    )
    model.resource_consumption = pyo.Param(
        model.item_ids,
        initialize=lambda mdl, i: params["resource_consumption"][i],
        within=pyo.Reals,
    )
    model.resource_capacity = pyo.Param(
        initialize=params["resource_capacity"],
        within=pyo.Reals,
    )
    model.production_capacity = pyo.Param(
        model.item_ids,
        initialize=lambda mdl, i: params["production_capacity"][i],
        within=pyo.Reals,
    )

    model.production = pyo.Var(
        model.item_ids,
        domain=pyo.NonNegativeReals,
    )

    model.resource_limit = pyo.Constraint(
        expr=sum(
            model.resource_consumption[i] * model.production[i]
            for i in model.item_ids
        ) <= model.resource_capacity
    )

    model.production_limits = pyo.Constraint(
        model.item_ids,
        rule=lambda mdl, i: (
            mdl.production[i] <= mdl.production_capacity[i]
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[i] * model.production[i]
            for i in model.item_ids
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