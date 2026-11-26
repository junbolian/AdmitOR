# IR: {"sets":{"foods":["Steak","Tofu","Chicken","Broccoli","Rice","Spinach"]},"params":{"protein_per_serving":"real[foods]","carb_per_serving":"real[foods]","calories_per_serving":"real[foods]","cost_per_serving":"real[foods]","protein_requirement":"real","carb_requirement":"real","calorie_requirement":"real"},"variables":{"servings":"nonnegative_integer[foods]"},"constraints":["sum(protein_per_serving[f]*servings[f] for f in foods) >= protein_requirement","sum(carb_per_serving[f]*servings[f] for f in foods) >= carb_requirement","sum(calories_per_serving[f]*servings[f] for f in foods) >= calorie_requirement"],"objective":"minimize sum(cost_per_serving[f]*servings[f] for f in foods)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Use integral portions, as required by the final problem sentence.

    Food-indexed inputs may be mappings keyed by food name or sequences in
    this order: Steak, Tofu, Chicken, Broccoli, Rice, Spinach.
    """
    foods = ("Steak", "Tofu", "Chicken", "Broccoli", "Rice", "Spinach")

    def food_values(values):
        if isinstance(values, Mapping):
            return {food: values[food] for food in foods}
        if len(values) != len(foods):
            raise ValueError("Each food-indexed input must contain six values.")
        return {food: values[position] for position, food in enumerate(foods)}

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.protein_per_serving = pyo.Param(
        model.foods,
        initialize=food_values(params["protein_per_serving"]),
        within=pyo.Reals,
    )
    model.carb_per_serving = pyo.Param(
        model.foods,
        initialize=food_values(params["carb_per_serving"]),
        within=pyo.Reals,
    )
    model.calories_per_serving = pyo.Param(
        model.foods,
        initialize=food_values(params["calories_per_serving"]),
        within=pyo.Reals,
    )
    model.cost_per_serving = pyo.Param(
        model.foods,
        initialize=food_values(params["cost_per_serving"]),
        within=pyo.Reals,
    )
    model.protein_requirement = pyo.Param(
        initialize=params["protein_requirement"], within=pyo.Reals
    )
    model.carb_requirement = pyo.Param(
        initialize=params["carb_requirement"], within=pyo.Reals
    )
    model.calorie_requirement = pyo.Param(
        initialize=params["calorie_requirement"], within=pyo.Reals
    )

    model.servings = pyo.Var(model.foods, domain=pyo.NonNegativeIntegers)

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein_per_serving[food] * model.servings[food]
            for food in model.foods
        ) >= model.protein_requirement
    )
    model.carb_minimum = pyo.Constraint(
        expr=sum(
            model.carb_per_serving[food] * model.servings[food]
            for food in model.foods
        ) >= model.carb_requirement
    )
    model.calorie_minimum = pyo.Constraint(
        expr=sum(
            model.calories_per_serving[food] * model.servings[food]
            for food in model.foods
        ) >= model.calorie_requirement
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost_per_serving[food] * model.servings[food]
            for food in model.foods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}