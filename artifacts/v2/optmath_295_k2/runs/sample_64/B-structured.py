# IR: {"sets":{"item_set":"0..14"},"params":{"profit_per_unit":"real[item_set]","resource_consumption":"real[item_set]","resource_capacity":"real","max_production":"real[item_set]"},"variables":{"production":"nonnegative continuous[item_set]"},"constraints":["sum(resource_consumption[i]*production[i] for i in item_set) <= resource_capacity","production[i] <= max_production[i] for each i in item_set"],"objective":"maximize sum(profit_per_unit[i]*production[i] for i in item_set)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.item_set = pyo.RangeSet(0, 14)

    model.profit_per_unit = pyo.Param(
        model.item_set,
        initialize={
            item: params["profit_per_unit"][item] for item in range(15)
        },
        within=pyo.Reals,
    )
    model.resource_consumption = pyo.Param(
        model.item_set,
        initialize={
            item: params["resource_consumption"][item] for item in range(15)
        },
        within=pyo.Reals,
    )
    model.resource_capacity = pyo.Param(
        initialize=params["resource_capacity"],
        within=pyo.Reals,
    )
    model.max_production = pyo.Param(
        model.item_set,
        initialize={
            item: params["max_production"][item] for item in range(15)
        },
        within=pyo.Reals,
    )

    model.production = pyo.Var(
        model.item_set,
        domain=pyo.NonNegativeReals,
    )

    model.resource_limit = pyo.Constraint(
        expr=sum(
            model.resource_consumption[item] * model.production[item]
            for item in model.item_set
        )
        <= model.resource_capacity
    )

    def production_limit_rule(instance, item):
        return instance.production[item] <= instance.max_production[item]

    model.production_limits = pyo.Constraint(
        model.item_set,
        rule=production_limit_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_per_unit[item] * model.production[item]
            for item in model.item_set
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}