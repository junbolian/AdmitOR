# IR:
# {
#   "sets": {"foods": ["Chicken", "Tuna", "Eggs", "Beef", "Rice", "Apples", "Bread"]},
#   "params": {
#     "protein_grams": "food-indexed protein; mapping or sequence in foods order",
#     "carb_grams": "food-indexed carbohydrates; mapping or sequence in foods order",
#     "calories": "food-indexed calories; mapping or sequence in foods order",
#     "prices": "food-indexed unit costs; mapping or sequence in foods order",
#     "protein_target": "minimum weekly protein",
#     "carb_target": "minimum weekly carbohydrates",
#     "calorie_target": "minimum weekly calories"
#   },
#   "decision_variables": {"quantity[food]": "nonnegative continuous real"},
#   "constraints": [
#     "sum(protein_grams[food] * quantity[food] for food in foods) >= protein_target",
#     "sum(carb_grams[food] * quantity[food] for food in foods) >= carb_target",
#     "sum(calories[food] * quantity[food] for food in foods) >= calorie_target"
#   ],
#   "objective": "minimize sum(prices[food] * quantity[food] for food in foods)"
# }

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ("Chicken", "Tuna", "Eggs", "Beef", "Rice", "Apples", "Bread")

    def by_food(values):
        if isinstance(values, Mapping):
            return {food: values[food] for food in foods}
        return {food: values[position] for position, food in enumerate(foods)}

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.protein_grams = pyo.Param(
        model.foods, initialize=by_food(params["protein_grams"])
    )
    model.carb_grams = pyo.Param(
        model.foods, initialize=by_food(params["carb_grams"])
    )
    model.calories = pyo.Param(
        model.foods, initialize=by_food(params["calories"])
    )
    model.prices = pyo.Param(
        model.foods, initialize=by_food(params["prices"])
    )
    model.protein_target = pyo.Param(initialize=params["protein_target"])
    model.carb_target = pyo.Param(initialize=params["carb_target"])
    model.calorie_target = pyo.Param(initialize=params["calorie_target"])

    model.quantity = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_requirement = pyo.Constraint(
        expr=sum(
            model.protein_grams[food] * model.quantity[food]
            for food in model.foods
        ) >= model.protein_target
    )
    model.carb_requirement = pyo.Constraint(
        expr=sum(
            model.carb_grams[food] * model.quantity[food]
            for food in model.foods
        ) >= model.carb_target
    )
    model.calorie_requirement = pyo.Constraint(
        expr=sum(
            model.calories[food] * model.quantity[food]
            for food in model.foods
        ) >= model.calorie_target
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.prices[food] * model.quantity[food]
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