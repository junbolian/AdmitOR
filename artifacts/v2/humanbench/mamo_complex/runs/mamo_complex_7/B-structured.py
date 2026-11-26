# IR: {"sets":{"foods":["Chicken","Rice","Vegetables","Bread","Almonds","Salmon"]},"params":{"protein":"real[foods]","carbs":"real[foods]","calories":"real[foods]","cost":"real[foods]","protein_requirement":"real","carb_requirement":"real","calorie_requirement":"real"},"variables":{"quantity":"nonnegative continuous[foods]"},"constraints":["sum(protein[f]*quantity[f] for f in foods) >= protein_requirement","sum(carbs[f]*quantity[f] for f in foods) >= carb_requirement","sum(calories[f]*quantity[f] for f in foods) >= calorie_requirement"],"objective":"minimize sum(cost[f]*quantity[f] for f in foods)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ("Chicken", "Rice", "Vegetables", "Bread", "Almonds", "Salmon")

    def food_data(values):
        """Accept food-name mappings or sequences in the declared food order."""
        if isinstance(values, Mapping):
            return {food: values[food] for food in foods}
        return {food: values[position] for position, food in enumerate(foods)}

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.protein = pyo.Param(
        model.foods, initialize=food_data(params["protein"]), within=pyo.Reals
    )
    model.carbs = pyo.Param(
        model.foods, initialize=food_data(params["carbs"]), within=pyo.Reals
    )
    model.calories = pyo.Param(
        model.foods, initialize=food_data(params["calories"]), within=pyo.Reals
    )
    model.cost = pyo.Param(
        model.foods, initialize=food_data(params["cost"]), within=pyo.Reals
    )
    model.protein_requirement = pyo.Param(
        initialize=params["protein_requirement"], within=pyo.Reals
    )
    model.carb_requirement = pyo.Param(
        initialize=params["carb_requirement"], within=pyo.Reals
    )
    model.calorie_requirement = pyo.Param(
        initialize=params["calorie_requirement"], within=pyo.Reals
    )

    model.quantity = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_target = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.quantity[food] for food in model.foods
        ) >= model.protein_requirement
    )
    model.carb_target = pyo.Constraint(
        expr=sum(
            model.carbs[food] * model.quantity[food] for food in model.foods
        ) >= model.carb_requirement
    )
    model.calorie_target = pyo.Constraint(
        expr=sum(
            model.calories[food] * model.quantity[food] for food in model.foods
        ) >= model.calorie_requirement
    )

    model.total_cost = pyo.Objective(
        expr=sum(model.cost[food] * model.quantity[food] for food in model.foods),
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