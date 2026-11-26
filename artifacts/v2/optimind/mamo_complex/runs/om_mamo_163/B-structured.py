# IR: {"sets":{"foods":["Eggs","Chicken","Tofu","Salmon","Brown Rice","Spinach"]},"params":{"costs":"cost per food","protein":"protein per food","carbs":"carbohydrates per food","calories":"calories per food","protein_req":"minimum protein","carb_req":"minimum carbohydrates","calorie_req":"minimum calories"},"variables":{"portions[food]":"nonnegative integer"},"constraints":["sum(protein[food]*portions[food]) >= protein_req","sum(carbs[food]*portions[food]) >= carb_req","sum(calories[food]*portions[food]) >= calorie_req"],"objective":"minimize sum(costs[food]*portions[food])"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Food data may be mappings keyed by food name or sequences in IR order."""
    foods = ("Eggs", "Chicken", "Tofu", "Salmon", "Brown Rice", "Spinach")

    def food_values(data):
        if isinstance(data, Mapping):
            return {food: data[food] for food in foods}
        return {food: data[position] for position, food in enumerate(foods)}

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.costs = pyo.Param(
        model.foods, initialize=food_values(params["costs"])
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
    model.protein_req = pyo.Param(initialize=params["protein_req"])
    model.carb_req = pyo.Param(initialize=params["carb_req"])
    model.calorie_req = pyo.Param(initialize=params["calorie_req"])

    model.portions = pyo.Var(model.foods, domain=pyo.NonNegativeIntegers)

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.portions[food]
            for food in model.foods
        ) >= model.protein_req
    )
    model.carb_minimum = pyo.Constraint(
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
            model.costs[food] * model.portions[food]
            for food in model.foods
        ),
        sense=pyo.minimize,
    )

    # APPsi raises RuntimeError when it cannot load a feasible solution.
    # Objective retrieval below is the sole success test.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}