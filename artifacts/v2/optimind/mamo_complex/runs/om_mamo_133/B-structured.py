# IR: {"sets":{"foods":["Eggs","Grains","Berries","Nuts","Salmon","Vegetables","Rice","Meat"]},"params":{"cost":"per-food real values","protein":"per-food real values","carbs":"per-food real values","calories":"per-food real values","protein_req":"real scalar","carb_req":"real scalar","calorie_req":"real scalar"},"variables":{"portions[food]":"nonnegative integer"},"constraints":["sum(protein[food]*portions[food]) >= protein_req","sum(carbs[food]*portions[food]) >= carb_req","sum(calories[food]*portions[food]) >= calorie_req"],"objective":"minimize sum(cost[food]*portions[food])"}
from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = (
        "Eggs",
        "Grains",
        "Berries",
        "Nuts",
        "Salmon",
        "Vegetables",
        "Rice",
        "Meat",
    )

    # Per-food inputs may be mappings keyed by food name or sequences
    # ordered as in foods.
    def food_values(values):
        if isinstance(values, Mapping):
            return {food: values[food] for food in foods}
        return {food: values[position] for position, food in enumerate(foods)}

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.cost = pyo.Param(
        model.foods, initialize=food_values(params["cost"]), within=pyo.Reals
    )
    model.protein = pyo.Param(
        model.foods, initialize=food_values(params["protein"]), within=pyo.Reals
    )
    model.carbs = pyo.Param(
        model.foods, initialize=food_values(params["carbs"]), within=pyo.Reals
    )
    model.calories = pyo.Param(
        model.foods, initialize=food_values(params["calories"]), within=pyo.Reals
    )
    model.protein_req = pyo.Param(
        initialize=params["protein_req"], within=pyo.Reals
    )
    model.carb_req = pyo.Param(
        initialize=params["carb_req"], within=pyo.Reals
    )
    model.calorie_req = pyo.Param(
        initialize=params["calorie_req"], within=pyo.Reals
    )

    model.portions = pyo.Var(model.foods, domain=pyo.NonNegativeIntegers)

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.portions[food]
            for food in model.foods
        ) >= model.protein_req
    )
    model.carbohydrate_minimum = pyo.Constraint(
        expr=sum(
            model.carbs[food] * model.portions[food]
            for food in model.foods
        ) >= model.carb_req
    )
    model.calorie_minimum = pyo.Constraint(
        expr=sum(
            model.calories[food] * model.portions[food]
            for food in model.foods
        ) >= model.calorie_req
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[food] * model.portions[food]
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