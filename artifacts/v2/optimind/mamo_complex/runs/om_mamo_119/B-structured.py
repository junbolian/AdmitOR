# IR: {"sets":{"foods":["Steak","Apples","Eggs","Chicken","Tofu"]},"params":{"cost_per_unit":"food-name mapping or sequence in foods order","protein_per_unit":"food-name mapping or sequence in foods order","carbs_per_unit":"food-name mapping or sequence in foods order","calories_per_unit":"food-name mapping or sequence in foods order","min_protein":"number","min_carbs":"number","min_calories":"number"},"variables":{"portions[food]":"nonnegative integer"},"constraints":["sum(protein_per_unit[food]*portions[food] for food in foods) >= min_protein","sum(carbs_per_unit[food]*portions[food] for food in foods) >= min_carbs","sum(calories_per_unit[food]*portions[food] for food in foods) >= min_calories"],"objective":"minimize sum(cost_per_unit[food]*portions[food] for food in foods)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ("Steak", "Apples", "Eggs", "Chicken", "Tofu")

    def food_mapping(values):
        """Normalize food-name mappings or positional sequences."""
        if isinstance(values, Mapping):
            return {food: values[food] for food in foods}
        if len(values) != len(foods):
            raise ValueError("Each food parameter must contain five values.")
        return {food: values[position] for position, food in enumerate(foods)}

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.cost_per_unit = pyo.Param(
        model.foods,
        initialize=food_mapping(params["cost_per_unit"]),
        within=pyo.Reals,
    )
    model.protein_per_unit = pyo.Param(
        model.foods,
        initialize=food_mapping(params["protein_per_unit"]),
        within=pyo.Reals,
    )
    model.carbs_per_unit = pyo.Param(
        model.foods,
        initialize=food_mapping(params["carbs_per_unit"]),
        within=pyo.Reals,
    )
    model.calories_per_unit = pyo.Param(
        model.foods,
        initialize=food_mapping(params["calories_per_unit"]),
        within=pyo.Reals,
    )
    model.min_protein = pyo.Param(
        initialize=params["min_protein"], within=pyo.Reals
    )
    model.min_carbs = pyo.Param(
        initialize=params["min_carbs"], within=pyo.Reals
    )
    model.min_calories = pyo.Param(
        initialize=params["min_calories"], within=pyo.Reals
    )

    model.portions = pyo.Var(model.foods, domain=pyo.NonNegativeIntegers)

    model.protein_requirement = pyo.Constraint(
        expr=sum(
            model.protein_per_unit[food] * model.portions[food]
            for food in model.foods
        ) >= model.min_protein
    )
    model.carbs_requirement = pyo.Constraint(
        expr=sum(
            model.carbs_per_unit[food] * model.portions[food]
            for food in model.foods
        ) >= model.min_carbs
    )
    model.calorie_requirement = pyo.Constraint(
        expr=sum(
            model.calories_per_unit[food] * model.portions[food]
            for food in model.foods
        ) >= model.min_calories
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost_per_unit[food] * model.portions[food]
            for food in model.foods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Continue to objective retrieval only for a missing feasible solution.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}