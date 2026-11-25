# IR: {"sets":{"foods":"food_0,...,food_14","nutrients":"nutrient_0,...,nutrient_8"},"params":{"cost_per_serving":"cost[food]","nutrient_min":"minimum[nutrient]","nutrient_max":"maximum[nutrient]","volume_capacity":"capacity","volume_per_serving":"volume[food]","nutrient_per_serving":"required food-by-nutrient coefficient matrix; absent from the supplied specification"},"decision_variables":{"servings[food]":"continuous, nonnegative"},"constraints":["minimum[nutrient] <= sum(nutrient_per_serving[food,nutrient]*servings[food] for food in foods) <= maximum[nutrient], for every nutrient","sum(volume[food]*servings[food] for food in foods) <= capacity"],"objective":"minimize sum(cost[food]*servings[food] for food in foods)"}
#
# The supplied problem specifies only six of the 135 nutrient coefficients.
# The five listed parameters do not determine the remaining coefficients.
# Consequently, no mathematically valid correction can produce the requested
# optimum from those parameters alone. Fabricating the matrix or omitting the
# nutrient constraints would solve a different problem.
#
# This script solves the stated model when the missing matrix is supplied as
# params["nutrient_per_serving"]; otherwise it returns an explicit failure.
# Vectors may be sequences or dictionaries keyed by food/nutrient names.
# The matrix must be food-major, with sequence rows or named dictionary rows.

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _entry(data, position, label):
    if isinstance(data, Mapping):
        return data[label]
    return data[position]


def solve(params):
    cost_data = params["cost_per_serving"]
    minimum_data = params["nutrient_min"]
    maximum_data = params["nutrient_max"]
    capacity = params["volume_capacity"]
    volume_data = params["volume_per_serving"]

    if "nutrient_per_serving" not in params:
        return {"objective": None, "status": "missing_nutrient_matrix"}

    nutrient_data = params["nutrient_per_serving"]
    foods = [f"food_{idx}" for idx in range(15)]
    nutrients = [f"nutrient_{idx}" for idx in range(9)]

    costs = {
        food: _entry(cost_data, idx, food)
        for idx, food in enumerate(foods)
    }
    volumes = {
        food: _entry(volume_data, idx, food)
        for idx, food in enumerate(foods)
    }
    minimums = {
        nutrient: _entry(minimum_data, idx, nutrient)
        for idx, nutrient in enumerate(nutrients)
    }
    maximums = {
        nutrient: _entry(maximum_data, idx, nutrient)
        for idx, nutrient in enumerate(nutrients)
    }
    coefficients = {}
    for food_idx, food in enumerate(foods):
        row = _entry(nutrient_data, food_idx, food)
        for nutrient_idx, nutrient in enumerate(nutrients):
            coefficients[food, nutrient] = _entry(
                row, nutrient_idx, nutrient
            )

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)
    model.nutrients = pyo.Set(initialize=nutrients, ordered=True)

    model.cost = pyo.Param(model.foods, initialize=costs)
    model.volume = pyo.Param(model.foods, initialize=volumes)
    model.minimum_requirement = pyo.Param(
        model.nutrients, initialize=minimums
    )
    model.maximum_requirement = pyo.Param(
        model.nutrients, initialize=maximums
    )
    model.capacity = pyo.Param(initialize=capacity)
    model.nutrient_amount = pyo.Param(
        model.foods, model.nutrients, initialize=coefficients
    )
    model.servings = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    def nutrient_rule(instance, nutrient):
        amount = sum(
            instance.nutrient_amount[food, nutrient]
            * instance.servings[food]
            for food in instance.foods
        )
        return (
            instance.minimum_requirement[nutrient],
            amount,
            instance.maximum_requirement[nutrient],
        )

    model.nutrient_limits = pyo.Constraint(
        model.nutrients, rule=nutrient_rule
    )
    model.volume_limit = pyo.Constraint(
        expr=sum(
            model.volume[food] * model.servings[food]
            for food in model.foods
        ) <= model.capacity
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[food] * model.servings[food]
            for food in model.foods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}