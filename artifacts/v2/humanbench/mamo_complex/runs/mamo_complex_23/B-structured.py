# IR: {"sets":{"foods":["Beef","Pasta","Broccoli","Chicken","Apple","Pork","Lentils","Eggs","Cheese"]},"params":{"cost":"params['cost'], food-keyed mapping or sequence in foods order","protein":"params['protein'], food-keyed mapping or sequence in foods order","carbs":"params['carbs'], food-keyed mapping or sequence in foods order","calories":"params['calories'], food-keyed mapping or sequence in foods order","req_protein":"params['req_protein']","req_carbs":"params['req_carbs']","req_calories":"params['req_calories']"},"variables":{"servings[food]":"nonnegative continuous"},"constraints":["sum(protein[food]*servings[food] for food in foods) >= req_protein","sum(carbs[food]*servings[food] for food in foods) >= req_carbs","sum(calories[food]*servings[food] for food in foods) >= req_calories"],"objective":"minimize sum(cost[food]*servings[food] for food in foods)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = (
        "Beef",
        "Pasta",
        "Broccoli",
        "Chicken",
        "Apple",
        "Pork",
        "Lentils",
        "Eggs",
        "Cheese",
    )

    def food_values(values):
        if isinstance(values, Mapping):
            return {food: values[food] for food in foods}
        if len(values) != len(foods):
            raise ValueError("Food parameter sequences must contain nine values.")
        return {food: values[position] for position, food in enumerate(foods)}

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.cost = pyo.Param(
        model.foods, initialize=food_values(params["cost"])
    )
    model.protein = pyo.Param(
        model.foods, initialize=food_values(params["protein"])
    )
    model.carbs = pyo.Param(
        model.foods, initialize=food_values(params["carbs"])
    )
    model.calories = pyo.Param(
        model.foods, initialize=food_values(params["calories"])
    )
    model.req_protein = pyo.Param(initialize=params["req_protein"])
    model.req_carbs = pyo.Param(initialize=params["req_carbs"])
    model.req_calories = pyo.Param(initialize=params["req_calories"])

    model.servings = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_requirement = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.servings[food]
            for food in model.foods
        ) >= model.req_protein
    )
    model.carbohydrate_requirement = pyo.Constraint(
        expr=sum(
            model.carbs[food] * model.servings[food]
            for food in model.foods
        ) >= model.req_carbs
    )
    model.calorie_requirement = pyo.Constraint(
        expr=sum(
            model.calories[food] * model.servings[food]
            for food in model.foods
        ) >= model.req_calories
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
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}