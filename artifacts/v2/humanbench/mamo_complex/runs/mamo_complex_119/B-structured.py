# IR: {"sets":{"foods":["Chicken","Rice","Lentils","Apples","Eggs","Broccoli"]},"params":{"protein":"grams/unit by food","carbs":"grams/unit by food","calories":"calories/unit by food","cost":"dollars/unit by food","protein_req":"minimum protein","carb_req":"minimum carbohydrates","calorie_req":"minimum calories"},"variables":{"quantity[food]":"nonnegative continuous"},"constraints":["sum(protein[food]*quantity[food]) >= protein_req","sum(carbs[food]*quantity[food]) >= carb_req","sum(calories[food]*quantity[food]) >= calorie_req"],"objective":"minimize sum(cost[food]*quantity[food])"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Food data may be mappings keyed by food name or sequences in food order."""
    foods = ("Chicken", "Rice", "Lentils", "Apples", "Eggs", "Broccoli")

    def by_food(values):
        if isinstance(values, Mapping):
            return {food: values[food] for food in foods}
        if len(values) != len(foods):
            raise ValueError("Each food-data sequence must contain six values.")
        return dict(zip(foods, values))

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.protein = pyo.Param(
        model.foods, initialize=by_food(params["protein"])
    )
    model.carbs = pyo.Param(
        model.foods, initialize=by_food(params["carbs"])
    )
    model.calories = pyo.Param(
        model.foods, initialize=by_food(params["calories"])
    )
    model.cost = pyo.Param(
        model.foods, initialize=by_food(params["cost"])
    )
    model.protein_req = pyo.Param(initialize=params["protein_req"])
    model.carb_req = pyo.Param(initialize=params["carb_req"])
    model.calorie_req = pyo.Param(initialize=params["calorie_req"])

    model.quantity = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.quantity[food]
            for food in model.foods
        ) >= model.protein_req
    )
    model.carbohydrate_minimum = pyo.Constraint(
        expr=sum(
            model.carbs[food] * model.quantity[food]
            for food in model.foods
        ) >= model.carb_req
    )
    model.calorie_minimum = pyo.Constraint(
        expr=sum(
            model.calories[food] * model.quantity[food]
            for food in model.foods
        ) >= model.calorie_req
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
    except RuntimeError as exc:
        if "feasible solution was not found" not in str(exc).lower():
            raise
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}