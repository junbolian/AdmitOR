# IR: {"sets":{"foods":["Steak","Apples","Eggs","Chicken","Tofu"]},"params":{"cost":"food-indexed unit costs; food-name mapping or sequence in foods order","protein":"food-indexed protein per unit; food-name mapping or sequence in foods order","carbs":"food-indexed carbohydrates per unit; food-name mapping or sequence in foods order","calories":"food-indexed calories per unit; food-name mapping or sequence in foods order","protein_req":"minimum protein","carb_req":"minimum carbohydrates","calorie_req":"minimum calories"},"variables":{"quantity[food]":"NonNegativeReals"},"constraints":["sum(protein[food]*quantity[food] for food in foods) >= protein_req","sum(carbs[food]*quantity[food] for food in foods) >= carb_req","sum(calories[food]*quantity[food] for food in foods) >= calorie_req"],"objective":"minimize sum(cost[food]*quantity[food] for food in foods)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ("Steak", "Apples", "Eggs", "Chicken", "Tofu")

    def food_indexed(values):
        if isinstance(values, Mapping):
            return {food: values[food] for food in foods}
        if len(values) != len(foods):
            raise ValueError("Food parameter sequences must contain five entries.")
        return {food: values[position] for position, food in enumerate(foods)}

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.cost = pyo.Param(
        model.foods, initialize=food_indexed(params["cost"])
    )
    model.protein = pyo.Param(
        model.foods, initialize=food_indexed(params["protein"])
    )
    model.carbs = pyo.Param(
        model.foods, initialize=food_indexed(params["carbs"])
    )
    model.calories = pyo.Param(
        model.foods, initialize=food_indexed(params["calories"])
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
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}