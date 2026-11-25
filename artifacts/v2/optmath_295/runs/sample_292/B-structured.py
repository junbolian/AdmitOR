# IR: {"sets":{"item_set":"0..24"},"params":{"profit_per_unit":"real[item_set]","resource_consumption_per_unit":"real[item_set]","resource_capacity":"real","production_upper_bounds":"real[item_set]"},"variables":{"production":"nonnegative real[item_set]"},"constraints":["sum(resource_consumption_per_unit[i]*production[i] for i in item_set) <= resource_capacity","production[i] <= production_upper_bounds[i] for i in item_set"],"objective":"maximize sum(profit_per_unit[i]*production[i] for i in item_set)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.item_set = pyo.RangeSet(0, 24)

    model.profit_per_unit = pyo.Param(
        model.item_set,
        initialize={
            i: params["profit_per_unit"][i] for i in model.item_set
        },
        within=pyo.Reals,
    )
    model.resource_consumption_per_unit = pyo.Param(
        model.item_set,
        initialize={
            i: params["resource_consumption_per_unit"][i]
            for i in model.item_set
        },
        within=pyo.Reals,
    )
    model.resource_capacity = pyo.Param(
        initialize=params["resource_capacity"],
        within=pyo.Reals,
    )
    model.production_upper_bounds = pyo.Param(
        model.item_set,
        initialize={
            i: params["production_upper_bounds"][i]
            for i in model.item_set
        },
        within=pyo.Reals,
    )

    model.production = pyo.Var(
        model.item_set,
        domain=pyo.NonNegativeReals,
    )

    model.resource_limit = pyo.Constraint(
        expr=sum(
            model.resource_consumption_per_unit[i] * model.production[i]
            for i in model.item_set
        ) <= model.resource_capacity
    )

    def production_limit_rule(instance, i):
        return instance.production[i] <= instance.production_upper_bounds[i]

    model.production_limits = pyo.Constraint(
        model.item_set,
        rule=production_limit_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_per_unit[i] * model.production[i]
            for i in model.item_set
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}