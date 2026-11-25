# IR: {"sets":{"products":["item_0", "...", "item_44"]},"params":{"profit_per_unit":"products -> real","resource_consumption_per_unit":"products -> real","resource_availability":"real","production_limit":"products -> real"},"variables":{"production":"products -> nonnegative real"},"constraints":["sum(resource_consumption_per_unit[i] * production[i] for i in products) <= resource_availability","production[i] <= production_limit[i] for each i in products"],"objective":"maximize sum(profit_per_unit[i] * production[i] for i in products)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = [f"item_{idx}" for idx in range(45)]

    profit = params["profit_per_unit"]
    consumption = params["resource_consumption_per_unit"]
    availability = params["resource_availability"]
    limits = params["production_limit"]

    # Accept either item-keyed mappings or sequences ordered item_0 to item_44.
    def indexed_values(values):
        if isinstance(values, (list, tuple)):
            return {item: values[idx] for idx, item in enumerate(products)}
        return {item: values[item] for item in products}

    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=products, ordered=True)

    model.profit_per_unit = pyo.Param(
        model.products,
        initialize=indexed_values(profit),
        within=pyo.Reals,
    )
    model.resource_consumption_per_unit = pyo.Param(
        model.products,
        initialize=indexed_values(consumption),
        within=pyo.Reals,
    )
    model.resource_availability = pyo.Param(
        initialize=availability,
        within=pyo.Reals,
    )
    model.production_limit = pyo.Param(
        model.products,
        initialize=indexed_values(limits),
        within=pyo.Reals,
    )

    model.production = pyo.Var(
        model.products,
        domain=pyo.NonNegativeReals,
    )

    model.resource_constraint = pyo.Constraint(
        expr=sum(
            model.resource_consumption_per_unit[item] * model.production[item]
            for item in model.products
        )
        <= model.resource_availability
    )

    def production_limit_rule(instance, item):
        return instance.production[item] <= instance.production_limit[item]

    model.production_limit_constraint = pyo.Constraint(
        model.products,
        rule=production_limit_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_per_unit[item] * model.production[item]
            for item in model.products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when its default solution loading finds no solution.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}