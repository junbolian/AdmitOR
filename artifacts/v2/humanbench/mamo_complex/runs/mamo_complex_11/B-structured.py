# IR: {"sets":{"foods":["Chicken","Rice","Beans","Avocado"]},"params":{"costs":"per-food unit costs","protein_content":"per-food protein","carb_content":"per-food carbohydrates","calorie_content":"per-food calories","protein_req":"minimum protein","carb_req":"minimum carbohydrates","calorie_req":"minimum calories"},"variables":{"quantity[food]":"nonnegative continuous"},"constraints":["sum(protein_content[f]*quantity[f]) >= protein_req","sum(carb_content[f]*quantity[f]) >= carb_req","sum(calorie_content[f]*quantity[f]) >= calorie_req"],"objective":"minimize sum(costs[f]*quantity[f])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Per-food inputs may be sequences in food order or dictionaries by food."""
    foods = ("Chicken", "Rice", "Beans", "Avocado")

    def food_values(values):
        if isinstance(values, dict):
            return {food: values[food] for food in foods}
        return {food: values[position] for position, food in enumerate(foods)}

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.unit_cost = pyo.Param(
        model.foods, initialize=food_values(params["costs"])
    )
    model.protein_per_unit = pyo.Param(
        model.foods, initialize=food_values(params["protein_content"])
    )
    model.carbs_per_unit = pyo.Param(
        model.foods, initialize=food_values(params["carb_content"])
    )
    model.calories_per_unit = pyo.Param(
        model.foods, initialize=food_values(params["calorie_content"])
    )
    model.required_protein = pyo.Param(initialize=params["protein_req"])
    model.required_carbs = pyo.Param(initialize=params["carb_req"])
    model.required_calories = pyo.Param(initialize=params["calorie_req"])

    model.quantity = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein_per_unit[food] * model.quantity[food]
            for food in model.foods
        ) >= model.required_protein
    )
    model.carb_minimum = pyo.Constraint(
        expr=sum(
            model.carbs_per_unit[food] * model.quantity[food]
            for food in model.foods
        ) >= model.required_carbs
    )
    model.calorie_minimum = pyo.Constraint(
        expr=sum(
            model.calories_per_unit[food] * model.quantity[food]
            for food in model.foods
        ) >= model.required_calories
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[food] * model.quantity[food]
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