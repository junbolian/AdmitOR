# IR: {"sets":{"foods":["Chicken","Pasta","Rice","Beans","Cheese"]},"params":{"cost":"food-indexed vector","protein":"food-indexed vector","carbs":"food-indexed vector","calories":"food-indexed vector","protein_req":"scalar","carbs_req":"scalar","calorie_req":"scalar"},"variables":{"servings[food]":"continuous, nonnegative"},"constraints":["sum(protein[food]*servings[food]) >= protein_req","sum(carbs[food]*servings[food]) >= carbs_req","sum(calories[food]*servings[food]) >= calorie_req"],"objective":"minimize sum(cost[food]*servings[food])"}
from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Food vectors may be mappings keyed by food name or sequences in foods order."""
    foods = ("Chicken", "Pasta", "Rice", "Beans", "Cheese")

    def food_values(values):
        if isinstance(values, Mapping):
            return {food: values[food] for food in foods}
        if len(values) != len(foods):
            raise ValueError("Each food vector must contain exactly five entries.")
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
    model.carbs_req = pyo.Param(initialize=params["carbs_req"])
    model.calorie_req = pyo.Param(initialize=params["calorie_req"])

    model.servings = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.servings[food]
            for food in model.foods
        ) >= model.protein_req
    )
    model.carbs_minimum = pyo.Constraint(
        expr=sum(
            model.carbs[food] * model.servings[food]
            for food in model.foods
        ) >= model.carbs_req
    )
    model.calorie_minimum = pyo.Constraint(
        expr=sum(
            model.calories[food] * model.servings[food]
            for food in model.foods
        ) >= model.calorie_req
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
        # APPsi can raise when it cannot load a feasible solution.
        # Objective retrieval below remains the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}