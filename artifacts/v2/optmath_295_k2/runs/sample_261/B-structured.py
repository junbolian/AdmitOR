# IR: {"sets":{"foods":"food_0..food_14","nutrients":"nutrient_0..nutrient_8"},"params":{"cost_per_serving":"foods -> real, from params","nutrient_min":"nutrients -> real, from params","nutrient_max":"nutrients -> real, from params","volume_capacity":"real, from params","volume_per_serving":"foods -> real, from params","nutrient_per_serving":"foods x nutrients -> real; required coefficient matrix, omitted from the problem"},"variables":{"servings":"foods -> nonnegative continuous"},"constraints":["For each nutrient n: sum_f nutrient_per_serving[f,n]*servings[f] >= nutrient_min[n]","For each nutrient n: sum_f nutrient_per_serving[f,n]*servings[f] <= nutrient_max[n]","sum_f volume_per_serving[f]*servings[f] <= volume_capacity"],"objective":"minimize sum_f cost_per_serving[f]*servings[f]","missing_data_behavior":"Return objective=null and status=missing_nutrient_matrix if nutrient_per_serving is absent."}

# The reported failure is caused by missing problem data, not a solver bug.
# The five listed parameters do not specify the 15-by-9 nutrient matrix.
# Six example coefficients cannot determine the other 129 coefficients.
# Consequently, no script can compute the specified optimum from those five
# parameters alone without inventing data. This implementation solves the
# exact formulation if params["nutrient_per_serving"] is additionally supplied
# as a food-major matrix, nested mapping, or (food, nutrient)-keyed mapping.

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _entry(data, label, position):
    if isinstance(data, Mapping):
        return data[label] if label in data else data[position]
    return data[position]


def _coefficient(data, food, food_idx, nutrient, nutrient_idx):
    if isinstance(data, Mapping):
        if (food, nutrient) in data:
            return data[food, nutrient]
        if (food_idx, nutrient_idx) in data:
            return data[food_idx, nutrient_idx]
    row = _entry(data, food, food_idx)
    return _entry(row, nutrient, nutrient_idx)


def solve(params):
    cost_data = params["cost_per_serving"]
    minimum_data = params["nutrient_min"]
    maximum_data = params["nutrient_max"]
    capacity_data = params["volume_capacity"]
    volume_data = params["volume_per_serving"]

    if (
        "nutrient_per_serving" not in params
        or params["nutrient_per_serving"] is None
    ):
        return {"objective": None, "status": "missing_nutrient_matrix"}

    nutrient_data = params["nutrient_per_serving"]
    foods = [f"food_{idx}" for idx in range(15)]
    nutrients = [f"nutrient_{idx}" for idx in range(9)]

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)
    model.nutrients = pyo.Set(initialize=nutrients, ordered=True)

    model.food_cost = pyo.Param(
        model.foods,
        initialize={
            food: _entry(cost_data, food, idx)
            for idx, food in enumerate(foods)
        },
    )
    model.food_volume = pyo.Param(
        model.foods,
        initialize={
            food: _entry(volume_data, food, idx)
            for idx, food in enumerate(foods)
        },
    )
    model.minimum_amount = pyo.Param(
        model.nutrients,
        initialize={
            nutrient: _entry(minimum_data, nutrient, idx)
            for idx, nutrient in enumerate(nutrients)
        },
    )
    model.maximum_amount = pyo.Param(
        model.nutrients,
        initialize={
            nutrient: _entry(maximum_data, nutrient, idx)
            for idx, nutrient in enumerate(nutrients)
        },
    )
    model.volume_capacity = pyo.Param(initialize=capacity_data)
    model.nutrient_content = pyo.Param(
        model.foods,
        model.nutrients,
        initialize={
            (food, nutrient): _coefficient(
                nutrient_data, food, food_idx, nutrient, nutrient_idx
            )
            for food_idx, food in enumerate(foods)
            for nutrient_idx, nutrient in enumerate(nutrients)
        },
    )

    model.servings = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    def nutrient_lower_rule(instance, nutrient):
        return sum(
            instance.nutrient_content[food, nutrient]
            * instance.servings[food]
            for food in instance.foods
        ) >= instance.minimum_amount[nutrient]

    def nutrient_upper_rule(instance, nutrient):
        return sum(
            instance.nutrient_content[food, nutrient]
            * instance.servings[food]
            for food in instance.foods
        ) <= instance.maximum_amount[nutrient]

    model.nutrient_lower_bounds = pyo.Constraint(
        model.nutrients, rule=nutrient_lower_rule
    )
    model.nutrient_upper_bounds = pyo.Constraint(
        model.nutrients, rule=nutrient_upper_rule
    )
    model.volume_limit = pyo.Constraint(
        expr=sum(
            model.food_volume[food] * model.servings[food]
            for food in model.foods
        ) <= model.volume_capacity
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.food_cost[food] * model.servings[food]
            for food in model.foods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # APPsi raises when a feasible solution cannot be loaded.
        # Do not mask unrelated RuntimeErrors.
        if any(model.servings[food].value is not None for food in model.foods):
            raise
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}