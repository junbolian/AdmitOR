# IR: {"sets":{"item_set":["item_0","item_1","item_2","item_3","item_4","item_5","item_6","item_7","item_8","item_9","item_10","item_11","item_12"]},"params":{"profit":"item-indexed real","resource_rate":"item-indexed nonnegative real","resource_capacity":"nonnegative real","production_capacity":"item-indexed nonnegative real"},"variables":{"production[item]":"nonnegative continuous"},"constraints":["sum(resource_rate[item] * production[item] for item in item_set) <= resource_capacity","production[item] <= production_capacity[item] for each item in item_set"],"objective":"maximize sum(profit[item] * production[item] for item in item_set)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using item-name-keyed mappings for indexed parameters."""
    model = pyo.ConcreteModel()

    model.item_set = pyo.Set(
        initialize=[f"item_{item_index}" for item_index in range(13)],
        ordered=True,
    )

    model.profit = pyo.Param(
        model.item_set,
        initialize={
            item: params["profit"][item]
            for item in model.item_set
        },
        within=pyo.Reals,
    )
    model.resource_rate = pyo.Param(
        model.item_set,
        initialize={
            item: params["resource_rate"][item]
            for item in model.item_set
        },
        within=pyo.NonNegativeReals,
    )
    model.resource_capacity = pyo.Param(
        initialize=params["resource_capacity"],
        within=pyo.NonNegativeReals,
    )
    model.production_capacity = pyo.Param(
        model.item_set,
        initialize={
            item: params["production_capacity"][item]
            for item in model.item_set
        },
        within=pyo.NonNegativeReals,
    )

    model.production = pyo.Var(
        model.item_set,
        domain=pyo.NonNegativeReals,
    )

    model.resource_limit = pyo.Constraint(
        expr=sum(
            model.resource_rate[item] * model.production[item]
            for item in model.item_set
        ) <= model.resource_capacity
    )

    def production_limit_rule(current_model, item):
        return (
            current_model.production[item]
            <= current_model.production_capacity[item]
        )

    model.production_limit = pyo.Constraint(
        model.item_set,
        rule=production_limit_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[item] * model.production[item]
            for item in model.item_set
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # A missing loadable solution is handled by objective retrieval.
        pass

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}