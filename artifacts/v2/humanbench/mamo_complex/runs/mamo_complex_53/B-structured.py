# IR: {"sets":{"foods":["Chicken","Oats","Tofu","Rice","Beef","Salmon"]},"params":{"protein":"food-indexed","carbs":"food-indexed","calories":"food-indexed","cost":"food-indexed","protein_target":"scalar","carb_target":"scalar","calorie_target":"scalar"},"variables":{"quantity[food]":"NonNegativeReals"},"constraints":["sum(protein[food]*quantity[food]) >= protein_target","sum(carbs[food]*quantity[food]) >= carb_target","sum(calories[food]*quantity[food]) >= calorie_target"],"objective":"minimize sum(cost[food]*quantity[food])"}
from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ("Chicken", "Oats", "Tofu", "Rice", "Beef", "Salmon")

    def food_values(values):
        if isinstance(values, Mapping):
            return {food: values[food] for food in foods}
        if len(values) != len(foods):
            raise ValueError("Each food parameter must contain six entries.")
        return dict(zip(foods, values))

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.protein = pyo.Param(
        model.foods, initialize=food_values(params["protein"])
    )
    model.carbs = pyo.Param(
        model.foods, initialize=food_values(params["carbs"])
    )
    model.calories = pyo.Param(
        model.foods, initialize=food_values(params["calories"])
    )
    model.cost = pyo.Param(
        model.foods, initialize=food_values(params["cost"])
    )
    model.protein_target = pyo.Param(initialize=params["protein_target"])
    model.carb_target = pyo.Param(initialize=params["carb_target"])
    model.calorie_target = pyo.Param(initialize=params["calorie_target"])

    model.quantity = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_requirement = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.quantity[food]
            for food in model.foods
        ) >= model.protein_target
    )
    model.carb_requirement = pyo.Constraint(
        expr=sum(
            model.carbs[food] * model.quantity[food]
            for food in model.foods
        ) >= model.carb_target
    )
    model.calorie_requirement = pyo.Constraint(
        expr=sum(
            model.calories[food] * model.quantity[food]
            for food in model.foods
        ) >= model.calorie_target
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
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}