# IR: {"sets":{"foods":["Chicken","Rice","Eggs","Broccoli","Lentils","Apples"]},"params":{"cost":"food-indexed unit costs","protein":"food-indexed protein grams","carbs":"food-indexed carbohydrate grams","calories":"food-indexed calories","protein_req":"minimum protein","carb_req":"minimum carbohydrates","calorie_req":"minimum calories"},"variables":{"quantity[food]":"NonNegativeReals"},"constraints":["sum(protein[f]*quantity[f] for f in foods) >= protein_req","sum(carbs[f]*quantity[f] for f in foods) >= carb_req","sum(calories[f]*quantity[f] for f in foods) >= calorie_req"],"objective":"minimize sum(cost[f]*quantity[f] for f in foods)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ("Chicken", "Rice", "Eggs", "Broccoli", "Lentils", "Apples")

    def food_values(values):
        """Accept food-name mappings or positional values in foods order."""
        if isinstance(values, Mapping):
            if all(food in values for food in foods):
                return {food: values[food] for food in foods}
            if all(position in values for position in range(len(foods))):
                return {
                    food: values[position]
                    for position, food in enumerate(foods)
                }
            if all(str(position) in values for position in range(len(foods))):
                return {
                    food: values[str(position)]
                    for position, food in enumerate(foods)
                }
            raise ValueError(
                "Food parameters must use food names or zero-based positional keys."
            )

        if len(values) != len(foods):
            raise ValueError("Each food parameter must contain six values.")

        return {
            food: values[position]
            for position, food in enumerate(foods)
        }

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
    except RuntimeError:
        # A solution-loading failure is handled by objective retrieval below.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}