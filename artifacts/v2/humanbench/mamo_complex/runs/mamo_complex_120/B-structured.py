# IR: {"sets":{"foods":["Pasta","Avocado","Chicken","Tofu","Spinach","Cheese"]},"params":{"protein_grams":"real[foods]","carbs_grams":"real[foods]","calories":"real[foods]","cost":"real[foods]","protein_target":"real","carb_target":"real","calorie_target":"real"},"variables":{"quantity":"nonnegative continuous[foods]"},"constraints":["sum(protein_grams[f]*quantity[f] for f in foods) >= protein_target","sum(carbs_grams[f]*quantity[f] for f in foods) >= carb_target","sum(calories[f]*quantity[f] for f in foods) >= calorie_target"],"objective":"minimize sum(cost[f]*quantity[f] for f in foods)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Food vectors may be food-name mappings or sequences in IR food order."""
    foods = ("Pasta", "Avocado", "Chicken", "Tofu", "Spinach", "Cheese")

    def food_values(values):
        if isinstance(values, Mapping):
            return {food: values[food] for food in foods}
        return {food: values[position] for position, food in enumerate(foods)}

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.protein_grams = pyo.Param(
        model.foods,
        initialize=food_values(params["protein_grams"]),
        within=pyo.Reals,
    )
    model.carbs_grams = pyo.Param(
        model.foods,
        initialize=food_values(params["carbs_grams"]),
        within=pyo.Reals,
    )
    model.calories = pyo.Param(
        model.foods,
        initialize=food_values(params["calories"]),
        within=pyo.Reals,
    )
    model.cost = pyo.Param(
        model.foods,
        initialize=food_values(params["cost"]),
        within=pyo.Reals,
    )
    model.protein_target = pyo.Param(
        initialize=params["protein_target"], within=pyo.Reals
    )
    model.carb_target = pyo.Param(
        initialize=params["carb_target"], within=pyo.Reals
    )
    model.calorie_target = pyo.Param(
        initialize=params["calorie_target"], within=pyo.Reals
    )

    model.quantity = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_requirement = pyo.Constraint(
        expr=sum(
            model.protein_grams[food] * model.quantity[food]
            for food in model.foods
        ) >= model.protein_target
    )
    model.carb_requirement = pyo.Constraint(
        expr=sum(
            model.carbs_grams[food] * model.quantity[food]
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
            model.cost[food] * model.quantity[food]
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