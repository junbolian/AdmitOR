# IR: {"sets":{"foods":["Chicken","Rice","Apples","Steak","Lentils","Fish","Tofu","Cheese","Bread"]},"params":{"price":"food-indexed costs","protein":"food-indexed protein","carbs":"food-indexed carbohydrates","calories":"food-indexed calories","protein_req":"minimum protein","carbs_req":"minimum carbohydrates","calories_req":"minimum calories","input_format":"Food-indexed inputs are sequences in foods order or mappings keyed by food names, zero-based indices, or one-based indices; numeric mapping keys may be strings."},"variables":{"portions[food]":"nonnegative integer"},"constraints":["sum(protein[food]*portions[food]) >= protein_req","sum(carbs[food]*portions[food]) >= carbs_req","sum(calories[food]*portions[food]) >= calories_req"],"objective":"minimize sum(price[food]*portions[food])"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _food_data(values, foods):
    """Convert supported input indexing into a food-name-keyed dictionary."""
    if not isinstance(values, Mapping):
        if len(values) != len(foods):
            raise ValueError("Each food-indexed input must contain nine values.")
        return {food: values[position] for position, food in enumerate(foods)}

    if all(food in values for food in foods):
        return {food: values[food] for food in foods}

    for offset in (0, 1):
        numeric_keys = [position + offset for position in range(len(foods))]
        if all(key in values for key in numeric_keys):
            return {
                food: values[position + offset]
                for position, food in enumerate(foods)
            }

        string_keys = [str(key) for key in numeric_keys]
        if all(key in values for key in string_keys):
            return {
                food: values[str(position + offset)]
                for position, food in enumerate(foods)
            }

    raise ValueError(
        "Food inputs must use food names or consecutive numeric indices."
    )


def solve(params):
    foods = (
        "Chicken", "Rice", "Apples", "Steak", "Lentils",
        "Fish", "Tofu", "Cheese", "Bread",
    )

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.price = pyo.Param(
        model.foods, initialize=_food_data(params["price"], foods)
    )
    model.protein = pyo.Param(
        model.foods, initialize=_food_data(params["protein"], foods)
    )
    model.carbs = pyo.Param(
        model.foods, initialize=_food_data(params["carbs"], foods)
    )
    model.calories = pyo.Param(
        model.foods, initialize=_food_data(params["calories"], foods)
    )

    model.protein_req = pyo.Param(initialize=params["protein_req"])
    model.carbs_req = pyo.Param(initialize=params["carbs_req"])
    model.calories_req = pyo.Param(initialize=params["calories_req"])

    model.portions = pyo.Var(model.foods, domain=pyo.NonNegativeIntegers)

    model.protein_requirement = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.portions[food]
            for food in model.foods
        ) >= model.protein_req
    )
    model.carbs_requirement = pyo.Constraint(
        expr=sum(
            model.carbs[food] * model.portions[food]
            for food in model.foods
        ) >= model.carbs_req
    )
    model.calories_requirement = pyo.Constraint(
        expr=sum(
            model.calories[food] * model.portions[food]
            for food in model.foods
        ) >= model.calories_req
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.price[food] * model.portions[food]
            for food in model.foods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}