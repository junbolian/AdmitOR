# {
#   "sets": {"products": ["shirt", "short_sleeve", "casual"]},
#   "params": [
#     "labor_per_unit_shirt", "labor_per_unit_short_sleeve", "labor_per_unit_casual",
#     "material_per_unit_shirt", "material_per_unit_short_sleeve", "material_per_unit_casual",
#     "price_shirt", "price_short_sleeve", "price_casual",
#     "variable_cost_shirt", "variable_cost_short_sleeve", "variable_cost_casual",
#     "labor_capacity", "material_capacity",
#     "fixed_cost_shirt", "fixed_cost_short_sleeve", "fixed_cost_casual"
#   ],
#   "derived": {"production_limit[p]": "min(labor_capacity/labor_per_unit[p], material_capacity/material_per_unit[p])"},
#   "variables": {"production[p]": "nonnegative integer", "line_open[p]": "binary"},
#   "constraints": [
#     "sum(labor_per_unit[p]*production[p] for p in products) <= labor_capacity",
#     "sum(material_per_unit[p]*production[p] for p in products) <= material_capacity",
#     "production[p] <= production_limit[p]*line_open[p] for each p in products"
#   ],
#   "objective": "maximize sum((price[p]-variable_cost[p])*production[p]-fixed_cost[p]*line_open[p] for p in products)"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.Set(
        initialize=["shirt", "short_sleeve", "casual"],
        ordered=True,
    )

    model.labor_per_unit = pyo.Param(
        model.products,
        initialize={
            "shirt": params["labor_per_unit_shirt"],
            "short_sleeve": params["labor_per_unit_short_sleeve"],
            "casual": params["labor_per_unit_casual"],
        },
        within=pyo.PositiveReals,
    )
    model.material_per_unit = pyo.Param(
        model.products,
        initialize={
            "shirt": params["material_per_unit_shirt"],
            "short_sleeve": params["material_per_unit_short_sleeve"],
            "casual": params["material_per_unit_casual"],
        },
        within=pyo.PositiveReals,
    )
    model.price = pyo.Param(
        model.products,
        initialize={
            "shirt": params["price_shirt"],
            "short_sleeve": params["price_short_sleeve"],
            "casual": params["price_casual"],
        },
    )
    model.variable_cost = pyo.Param(
        model.products,
        initialize={
            "shirt": params["variable_cost_shirt"],
            "short_sleeve": params["variable_cost_short_sleeve"],
            "casual": params["variable_cost_casual"],
        },
    )
    model.fixed_cost = pyo.Param(
        model.products,
        initialize={
            "shirt": params["fixed_cost_shirt"],
            "short_sleeve": params["fixed_cost_short_sleeve"],
            "casual": params["fixed_cost_casual"],
        },
    )
    model.labor_capacity = pyo.Param(
        initialize=params["labor_capacity"],
        within=pyo.NonNegativeReals,
    )
    model.material_capacity = pyo.Param(
        initialize=params["material_capacity"],
        within=pyo.NonNegativeReals,
    )

    model.production_limit = pyo.Param(
        model.products,
        initialize={
            product: min(
                pyo.value(model.labor_capacity)
                / pyo.value(model.labor_per_unit[product]),
                pyo.value(model.material_capacity)
                / pyo.value(model.material_per_unit[product]),
            )
            for product in model.products
        },
    )

    model.production = pyo.Var(
        model.products,
        domain=pyo.NonNegativeIntegers,
    )
    model.line_open = pyo.Var(
        model.products,
        domain=pyo.Binary,
    )

    model.labor_constraint = pyo.Constraint(
        expr=sum(
            model.labor_per_unit[product] * model.production[product]
            for product in model.products
        )
        <= model.labor_capacity
    )
    model.material_constraint = pyo.Constraint(
        expr=sum(
            model.material_per_unit[product] * model.production[product]
            for product in model.products
        )
        <= model.material_capacity
    )

    def line_activation_rule(instance, product):
        return (
            instance.production[product]
            <= instance.production_limit[product] * instance.line_open[product]
        )

    model.line_activation_constraint = pyo.Constraint(
        model.products,
        rule=line_activation_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            (model.price[product] - model.variable_cost[product])
            * model.production[product]
            - model.fixed_cost[product] * model.line_open[product]
            for product in model.products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}