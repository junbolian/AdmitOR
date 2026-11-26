# IR: {"sets":{"foods":["Chicken","Rice","Eggs","Beans","Spinach","Corn","Beef","Broccoli"]},"params":{"food_cost":"per-food costs","protein_content":"per-food protein","carb_content":"per-food carbohydrates","calorie_content":"per-food calories","protein_requirement":"weekly protein minimum","carb_requirement":"weekly carbohydrate minimum","calorie_requirement":"weekly calorie minimum"},"variables":{"quantity[food]":"NonNegativeReals"},"constraints":["sum(protein_content[food]*quantity[food]) >= protein_requirement","sum(carb_content[food]*quantity[food]) >= carb_requirement","sum(calorie_content[food]*quantity[food]) >= calorie_requirement"],"objective":"minimize sum(food_cost[food]*quantity[food])"}
from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept per-food sequences in listed order or mappings keyed by food name."""
    foods = (
        "Chicken", "Rice", "Eggs", "Beans",
        "Spinach", "Corn", "Beef", "Broccoli",
    )

    def food_values(values):
        if isinstance(values, Mapping):
            return {food: values[food] for food in foods}
        return {food: values[position] for position, food in enumerate(foods)}

    costs = food_values(params["food_cost"])
    proteins = food_values(params["protein_content"])
    carbohydrates = food_values(params["carb_content"])
    calories = food_values(params["calorie_content"])
    protein_minimum = params["protein_requirement"]
    carb_minimum = params["carb_requirement"]
    calorie_minimum = params["calorie_requirement"]

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.food_cost = pyo.Param(
        model.foods, initialize=costs, within=pyo.Reals
    )
    model.protein_content = pyo.Param(
        model.foods, initialize=proteins, within=pyo.Reals
    )
    model.carb_content = pyo.Param(
        model.foods, initialize=carbohydrates, within=pyo.Reals
    )
    model.calorie_content = pyo.Param(
        model.foods, initialize=calories, within=pyo.Reals
    )
    model.protein_requirement = pyo.Param(
        initialize=protein_minimum, within=pyo.Reals
    )
    model.carb_requirement = pyo.Param(
        initialize=carb_minimum, within=pyo.Reals
    )
    model.calorie_requirement = pyo.Param(
        initialize=calorie_minimum, within=pyo.Reals
    )

    model.quantity = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_minimum_constraint = pyo.Constraint(
        expr=sum(
            model.protein_content[food] * model.quantity[food]
            for food in model.foods
        ) >= model.protein_requirement
    )
    model.carb_minimum_constraint = pyo.Constraint(
        expr=sum(
            model.carb_content[food] * model.quantity[food]
            for food in model.foods
        ) >= model.carb_requirement
    )
    model.calorie_minimum_constraint = pyo.Constraint(
        expr=sum(
            model.calorie_content[food] * model.quantity[food]
            for food in model.foods
        ) >= model.calorie_requirement
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.food_cost[food] * model.quantity[food]
            for food in model.foods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}