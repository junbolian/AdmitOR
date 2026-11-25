# IR: {"sets":{"products":["item_0", "...", "item_44"]},"params":{"profit_per_unit":"real[products], from params","resource_consumption_per_unit":"real[products], from params","resource_availability":"real, from params","production_limit":"real[products], from params"},"variables":{"production":"nonnegative continuous[products]"},"constraints":["sum(resource_consumption_per_unit[i] * production[i] for i in products) <= resource_availability","production[i] <= production_limit[i] for each i in products"],"objective":"maximize sum(profit_per_unit[i] * production[i] for i in products)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Indexed inputs may be item-keyed mappings or sequences in item order."""
    products = [f"item_{product_idx}" for product_idx in range(45)]

    def indexed_values(values):
        if isinstance(values, Mapping):
            return {product: values[product] for product in products}
        return {
            product: values[product_idx]
            for product_idx, product in enumerate(products)
        }

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=products, ordered=True)

    model.profit_per_unit = pyo.Param(
        model.products,
        initialize=indexed_values(params["profit_per_unit"]),
        within=pyo.Reals,
    )
    model.resource_consumption_per_unit = pyo.Param(
        model.products,
        initialize=indexed_values(params["resource_consumption_per_unit"]),
        within=pyo.Reals,
    )
    model.resource_availability = pyo.Param(
        initialize=params["resource_availability"],
        within=pyo.Reals,
    )
    model.production_limit = pyo.Param(
        model.products,
        initialize=indexed_values(params["production_limit"]),
        within=pyo.Reals,
    )

    model.production = pyo.Var(
        model.products,
        domain=pyo.NonNegativeReals,
    )

    model.resource_constraint = pyo.Constraint(
        expr=sum(
            model.resource_consumption_per_unit[product]
            * model.production[product]
            for product in model.products
        )
        <= model.resource_availability
    )

    def production_limit_rule(instance, product):
        return (
            instance.production[product]
            <= instance.production_limit[product]
        )

    model.production_limit_constraint = pyo.Constraint(
        model.products,
        rule=production_limit_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_per_unit[product] * model.production[product]
            for product in model.products
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