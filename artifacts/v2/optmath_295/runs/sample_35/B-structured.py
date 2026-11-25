# IR: {"sets":{"item_set":["item_0","item_1","item_2","item_3","item_4","item_5","item_6","item_7","item_8","item_9","item_10"]},"params":{"profit_per_unit":"real[item_set]","resource_consumption_per_unit":"real[item_set]","resource_capacity":"real","production_upper_limits":"real[item_set]"},"variables":{"production":"nonnegative continuous[item_set]"},"constraints":["sum(resource_consumption_per_unit[i]*production[i] for i in item_set) <= resource_capacity","production[i] <= production_upper_limits[i] for each i in item_set"],"objective":"maximize sum(profit_per_unit[i]*production[i] for i in item_set)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept item data as sequences or mappings keyed by labels or indices."""
    profit_data = params["profit_per_unit"]
    consumption_data = params["resource_consumption_per_unit"]
    capacity_data = params["resource_capacity"]
    upper_limit_data = params["production_upper_limits"]

    item_labels = tuple(f"item_{idx}" for idx in range(11))

    def item_value(data, item):
        idx = int(item.split("_")[1])
        if isinstance(data, Mapping):
            if item in data:
                return data[item]
            if idx in data:
                return data[idx]
            return data[str(idx)]
        return data[idx]

    model = pyo.ConcreteModel()
    model.item_set = pyo.Set(initialize=item_labels, ordered=True)

    model.profit_per_unit = pyo.Param(
        model.item_set,
        initialize={
            item: item_value(profit_data, item) for item in item_labels
        },
        within=pyo.Reals,
    )
    model.resource_consumption_per_unit = pyo.Param(
        model.item_set,
        initialize={
            item: item_value(consumption_data, item) for item in item_labels
        },
        within=pyo.Reals,
    )
    model.resource_capacity = pyo.Param(
        initialize=capacity_data,
        within=pyo.Reals,
    )
    model.production_upper_limits = pyo.Param(
        model.item_set,
        initialize={
            item: item_value(upper_limit_data, item) for item in item_labels
        },
        within=pyo.Reals,
    )

    model.production = pyo.Var(
        model.item_set,
        domain=pyo.NonNegativeReals,
    )

    model.resource_constraint = pyo.Constraint(
        expr=sum(
            model.resource_consumption_per_unit[item] * model.production[item]
            for item in model.item_set
        )
        <= model.resource_capacity
    )

    def production_limit_rule(instance, item):
        return (
            instance.production[item]
            <= instance.production_upper_limits[item]
        )

    model.production_limit_constraints = pyo.Constraint(
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
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}