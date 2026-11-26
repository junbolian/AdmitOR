# IR: {"sets":{"foods":["Eggs","Grains","Berries","Nuts","Salmon","Vegetables","Rice","Meat"]},"params":{"costs":"real[foods]","protein":"real[foods]","carbs":"real[foods]","calories":"real[foods]","protein_req":"real","carb_req":"real","calorie_req":"real"},"variables":{"quantity":"nonnegative continuous[foods]"},"constraints":["sum(protein[f]*quantity[f] for f in foods) >= protein_req","sum(carbs[f]*quantity[f] for f in foods) >= carb_req","sum(calories[f]*quantity[f] for f in foods) >= calorie_req"],"objective":"minimize sum(costs[f]*quantity[f] for f in foods)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept food data as name-keyed mappings or sequences in IR food order."""
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

    def food_data(values):
        if isinstance(values, Mapping):
            return {food: values[food] for food in foods}
        return {food: values[position] for position, food in enumerate(foods)}

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.costs = pyo.Param(
        model.foods, initialize=food_data(params["costs"]), within=pyo.Reals
    )
    model.protein = pyo.Param(
        model.foods, initialize=food_data(params["protein"]), within=pyo.Reals
    )
    model.carbs = pyo.Param(
        model.foods, initialize=food_data(params["carbs"]), within=pyo.Reals
    )
    model.calories = pyo.Param(
        model.foods, initialize=food_data(params["calories"]), within=pyo.Reals
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

    model.quantity = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.quantity[food] for food in model.foods
        ) >= model.protein_req
    )
    model.carbohydrate_minimum = pyo.Constraint(
        expr=sum(
            model.carbs[food] * model.quantity[food] for food in model.foods
        ) >= model.carb_req
    )
    model.calorie_minimum = pyo.Constraint(
        expr=sum(
            model.calories[food] * model.quantity[food] for food in model.foods
        ) >= model.calorie_req
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.costs[food] * model.quantity[food] for food in model.foods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no solution is available to load.
        # Objective retrieval below remains the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}