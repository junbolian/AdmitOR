# IR: {"sets":{"products":"item_0 through item_44"},"params":{"profit":"real[products], supplied as item-keyed mapping or ordered sequence","resource_coefficient":"real[products], supplied as item-keyed mapping or ordered sequence","resource_capacity":"real scalar","production_limit":"real[products], supplied as item-keyed mapping or ordered sequence"},"variables":{"production":"nonnegative continuous[products]"},"constraints":["sum(resource_coefficient[i] * production[i] for i in products) <= resource_capacity","production[i] <= production_limit[i] for each i in products"],"objective":"maximize sum(profit[i] * production[i] for i in products)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = [f"item_{idx}" for idx in range(45)]

    def indexed_data(values):
        if isinstance(values, Mapping):
            return {item: values[item] for item in products}
        return {
            item: values[idx]
            for idx, item in enumerate(products)
        }

    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=products, ordered=True)

    model.profit = pyo.Param(
        model.products,
        initialize=indexed_data(params["profit"]),
        within=pyo.Reals,
    )
    model.resource_coefficient = pyo.Param(
        model.products,
        initialize=indexed_data(params["resource_coefficient"]),
        within=pyo.Reals,
    )
    model.resource_capacity = pyo.Param(
        initialize=params["resource_capacity"],
        within=pyo.Reals,
    )
    model.production_limit = pyo.Param(
        model.products,
        initialize=indexed_data(params["production_limit"]),
        within=pyo.Reals,
    )

    model.production = pyo.Var(
        model.products,
        domain=pyo.NonNegativeReals,
    )

    model.resource_constraint = pyo.Constraint(
        expr=sum(
            model.resource_coefficient[item] * model.production[item]
            for item in model.products
        )
        <= model.resource_capacity
    )

    def production_limit_rule(mdl, item):
        return mdl.production[item] <= mdl.production_limit[item]

    model.production_limit_constraint = pyo.Constraint(
        model.products,
        rule=production_limit_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[item] * model.production[item]
            for item in model.products
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