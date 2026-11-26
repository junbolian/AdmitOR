# IR: {"sets":{"foods":["Chicken","Rice","Apples","Steak","Lentils","Fish","Tofu","Cheese","Bread"]},"params":{"protein_content":"foods -> real","carb_content":"foods -> real","calorie_content":"foods -> real","food_price":"foods -> real","protein_requirement":"real","carb_requirement":"real","calorie_requirement":"real"},"variables":{"quantity[food]":"continuous nonnegative"},"constraints":["sum(protein_content[food]*quantity[food] for food in foods) >= protein_requirement","sum(carb_content[food]*quantity[food] for food in foods) >= carb_requirement","sum(calorie_content[food]*quantity[food] for food in foods) >= calorie_requirement"],"objective":"minimize sum(food_price[food]*quantity[food] for food in foods)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = (
        "Chicken", "Rice", "Apples", "Steak", "Lentils",
        "Fish", "Tofu", "Cheese", "Bread",
    )

    # Food data may be mappings keyed by food name or sequences in foods order.
    def indexed_data(values):
        if isinstance(values, Mapping):
            return {food: values[food] for food in foods}
        if len(values) != len(foods):
            raise ValueError("Food data must contain exactly nine entries.")
        return {food: values[position] for position, food in enumerate(foods)}

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.protein_content = pyo.Param(
        model.foods,
        initialize=indexed_data(params["protein_content"]),
        within=pyo.Reals,
    )
    model.carb_content = pyo.Param(
        model.foods,
        initialize=indexed_data(params["carb_content"]),
        within=pyo.Reals,
    )
    model.calorie_content = pyo.Param(
        model.foods,
        initialize=indexed_data(params["calorie_content"]),
        within=pyo.Reals,
    )
    model.food_price = pyo.Param(
        model.foods,
        initialize=indexed_data(params["food_price"]),
        within=pyo.Reals,
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

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein_content[food] * model.quantity[food]
            for food in model.foods
        ) >= model.protein_requirement
    )
    model.carb_minimum = pyo.Constraint(
        expr=sum(
            model.carb_content[food] * model.quantity[food]
            for food in model.foods
        ) >= model.carb_requirement
    )
    model.calorie_minimum = pyo.Constraint(
        expr=sum(
            model.calorie_content[food] * model.quantity[food]
            for food in model.foods
        ) >= model.calorie_requirement
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.food_price[food] * model.quantity[food]
            for food in model.foods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}