# IR: {"sets":{"foods":["Chicken","Tofu","Rice","Avocado"]},"params":{"cost":"params['cost']: sequence in foods order or mapping keyed by food","protein":"params['protein']: sequence in foods order or mapping keyed by food","carbs":"params['carbs']: sequence in foods order or mapping keyed by food","calories":"params['calories']: sequence in foods order or mapping keyed by food","protein_req":"params['protein_req']","carb_req":"params['carb_req']","calorie_req":"params['calorie_req']"},"variables":{"portions[food]":"nonnegative integer"},"constraints":{"protein_minimum":"sum(protein[food]*portions[food] for food in foods) >= protein_req","carbohydrate_minimum":"sum(carbs[food]*portions[food] for food in foods) >= carb_req","calorie_minimum":"sum(calories[food]*portions[food] for food in foods) >= calorie_req"},"objective":{"sense":"minimize","expression":"sum(cost[food]*portions[food] for food in foods)"}}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ("Chicken", "Tofu", "Rice", "Avocado")

    def food_values(values):
        if isinstance(values, Mapping):
            return {food: values[food] for food in foods}
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
        # An infeasible solve can raise before loading a solution.
        # Determine success exclusively by objective retrievability below.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}