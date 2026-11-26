# IR: {"sets":{"FOODS":["Food_1","Food_2","Food_3","Food_4","Food_5","Food_6","Food_7"]},"params":{"cost":"real[FOODS]","protein":"real[FOODS]","carbs":"real[FOODS]","calories":"real[FOODS]","protein_req":"real","carb_req":"real","calorie_req":"real"},"variables":{"quantity":"nonnegative continuous[FOODS]"},"constraints":["sum(protein[f]*quantity[f] for f in FOODS) >= protein_req","sum(carbs[f]*quantity[f] for f in FOODS) >= carb_req","sum(calories[f]*quantity[f] for f in FOODS) >= calorie_req"],"objective":"minimize sum(cost[f]*quantity[f] for f in FOODS)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Indexed parameters accept either mappings keyed by Food_1,...,Food_7
    or sequences ordered Food_1,...,Food_7. Food quantities are divisible.
    """
    foods = tuple(f"Food_{position}" for position in range(1, 8))

    def food_values(values):
        if isinstance(values, Mapping):
            return {food: values[food] for food in foods}
        if len(values) != len(foods):
            raise ValueError("Each food parameter must contain seven values.")
        return {
            food: values[position]
            for position, food in enumerate(foods)
        }

    model = pyo.ConcreteModel()
    model.FOODS = pyo.Set(initialize=foods, ordered=True)

    model.cost = pyo.Param(
        model.FOODS, initialize=food_values(params["cost"]), within=pyo.Reals
    )
    model.protein = pyo.Param(
        model.FOODS, initialize=food_values(params["protein"]), within=pyo.Reals
    )
    model.carbs = pyo.Param(
        model.FOODS, initialize=food_values(params["carbs"]), within=pyo.Reals
    )
    model.calories = pyo.Param(
        model.FOODS, initialize=food_values(params["calories"]), within=pyo.Reals
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

    model.quantity = pyo.Var(model.FOODS, domain=pyo.NonNegativeReals)

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.quantity[food]
            for food in model.FOODS
        ) >= model.protein_req
    )
    model.carbohydrate_minimum = pyo.Constraint(
        expr=sum(
            model.carbs[food] * model.quantity[food]
            for food in model.FOODS
        ) >= model.carb_req
    )
    model.calorie_minimum = pyo.Constraint(
        expr=sum(
            model.calories[food] * model.quantity[food]
            for food in model.FOODS
        ) >= model.calorie_req
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[food] * model.quantity[food]
            for food in model.FOODS
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}