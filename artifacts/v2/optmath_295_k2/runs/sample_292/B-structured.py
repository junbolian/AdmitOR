# IR: {"sets":{"item_ids":"0..24"},"params":{"profit":"real[item_ids]","resource_coeff":"real[item_ids]","resource_capacity":"real scalar","upper_limit":"real[item_ids]"},"variables":{"production":"nonnegative continuous[item_ids]"},"constraints":["sum(resource_coeff[i]*production[i] for i in item_ids) <= resource_capacity","production[i] <= upper_limit[i] for each i in item_ids"],"objective":"maximize sum(profit[i]*production[i] for i in item_ids)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.item_ids = pyo.RangeSet(0, 24)

    model.profit = pyo.Param(
        model.item_ids,
        initialize={i: params["profit"][i] for i in model.item_ids},
        within=pyo.Reals,
    )
    model.resource_coeff = pyo.Param(
        model.item_ids,
        initialize={i: params["resource_coeff"][i] for i in model.item_ids},
        within=pyo.Reals,
    )
    model.resource_capacity = pyo.Param(
        initialize=params["resource_capacity"],
        within=pyo.Reals,
    )
    model.upper_limit = pyo.Param(
        model.item_ids,
        initialize={i: params["upper_limit"][i] for i in model.item_ids},
        within=pyo.Reals,
    )

    model.production = pyo.Var(
        model.item_ids,
        domain=pyo.NonNegativeReals,
    )

    model.resource_constraint = pyo.Constraint(
        expr=sum(
            model.resource_coeff[i] * model.production[i]
            for i in model.item_ids
        ) <= model.resource_capacity
    )

    def production_limit_rule(instance, i):
        return instance.production[i] <= instance.upper_limit[i]

    model.production_limits = pyo.Constraint(
        model.item_ids,
        rule=production_limit_rule,
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
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}