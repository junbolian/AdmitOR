# IR: {
#   "sets": {"P": ["shirt", "short_sleeve", "casual_cloth"]},
#   "params": {
#     "labor_per_unit[P]": "params['labor_per_unit']; positive",
#     "material_per_unit[P]": "params['material_per_unit']; positive",
#     "selling_price[P]": "params['selling_price']; real",
#     "variable_cost[P]": "params['variable_cost']; real",
#     "labor_capacity": "params['labor_capacity']; nonnegative",
#     "material_capacity": "params['material_capacity']; nonnegative",
#     "fixed_cost_shirt": "params['fixed_cost_shirt']; nonnegative",
#     "fixed_cost_short_sleeve": "params['fixed_cost_short_sleeve']; nonnegative",
#     "fixed_cost_casual_cloth": "params['fixed_cost_casual_cloth']; nonnegative"
#   },
#   "derived": {"U[p]": "min(labor_capacity/labor_per_unit[p], material_capacity/material_per_unit[p])"},
#   "variables": {"production[P]": "nonnegative integer", "equipment_used[P]": "binary"},
#   "constraints": [
#     "sum(labor_per_unit[p]*production[p] for p in P) <= labor_capacity",
#     "sum(material_per_unit[p]*production[p] for p in P) <= material_capacity",
#     "production[p] <= U[p]*equipment_used[p] for each p in P"
#   ],
#   "objective": "maximize sum((selling_price[p]-variable_cost[p])*production[p]-fixed_cost[p]*equipment_used[p] for p in P)",
#   "fixed_cost_mapping": {"shirt": "fixed_cost_shirt", "short_sleeve": "fixed_cost_short_sleeve", "casual_cloth": "fixed_cost_casual_cloth"}
# }

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Indexed inputs accept either dictionaries keyed by shirt, short_sleeve,
    and casual_cloth, or sequences in that product order.
    Production quantities are whole units.
    """
    products = ("shirt", "short_sleeve", "casual_cloth")

    def indexed_values(raw):
        if isinstance(raw, Mapping):
            return {product: raw[product] for product in products}
        if len(raw) != len(products):
            raise ValueError("Each indexed parameter must have three entries.")
        return dict(zip(products, raw))

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=products, ordered=True)

    model.labor_per_unit = pyo.Param(
        model.products,
        initialize=indexed_values(params["labor_per_unit"]),
        within=pyo.PositiveReals,
    )
    model.material_per_unit = pyo.Param(
        model.products,
        initialize=indexed_values(params["material_per_unit"]),
        within=pyo.PositiveReals,
    )
    model.selling_price = pyo.Param(
        model.products,
        initialize=indexed_values(params["selling_price"]),
        within=pyo.Reals,
    )
    model.variable_cost = pyo.Param(
        model.products,
        initialize=indexed_values(params["variable_cost"]),
        within=pyo.Reals,
    )
    model.labor_capacity = pyo.Param(
        initialize=params["labor_capacity"],
        within=pyo.NonNegativeReals,
    )
    model.material_capacity = pyo.Param(
        initialize=params["material_capacity"],
        within=pyo.NonNegativeReals,
    )
    model.fixed_cost = pyo.Param(
        model.products,
        initialize={
            "shirt": params["fixed_cost_shirt"],
            "short_sleeve": params["fixed_cost_short_sleeve"],
            "casual_cloth": params["fixed_cost_casual_cloth"],
        },
        within=pyo.NonNegativeReals,
    )

    production_limits = {
        product: min(
            pyo.value(model.labor_capacity)
            / pyo.value(model.labor_per_unit[product]),
            pyo.value(model.material_capacity)
            / pyo.value(model.material_per_unit[product]),
        )
        for product in products
    }
    model.production_limit = pyo.Param(
        model.products,
        initialize=production_limits,
        within=pyo.NonNegativeReals,
    )

    model.production = pyo.Var(
        model.products, domain=pyo.NonNegativeIntegers
    )
    model.equipment_used = pyo.Var(model.products, domain=pyo.Binary)

    model.labor_limit = pyo.Constraint(
        expr=sum(
            model.labor_per_unit[product] * model.production[product]
            for product in model.products
        )
        <= model.labor_capacity
    )
    model.material_limit = pyo.Constraint(
        expr=sum(
            model.material_per_unit[product] * model.production[product]
            for product in model.products
        )
        <= model.material_capacity
    )

    def equipment_link_rule(instance, product):
        return (
            instance.production[product]
            <= instance.production_limit[product]
            * instance.equipment_used[product]
        )

    model.equipment_link = pyo.Constraint(
        model.products, rule=equipment_link_rule
    )
    model.profit = pyo.Objective(
        expr=sum(
            (
                model.selling_price[product]
                - model.variable_cost[product]
            )
            * model.production[product]
            - model.fixed_cost[product] * model.equipment_used[product]
            for product in model.products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}