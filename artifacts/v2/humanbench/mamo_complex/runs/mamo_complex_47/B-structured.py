# IR: {"sets":{"foods":["Eggs","Chicken","Tofu","Salmon","Brown Rice","Spinach"]},"params":{"costs":"cost per serving, indexed by foods","protein_coeffs":"protein per serving, indexed by foods","carb_coeffs":"carbohydrates per serving, indexed by foods","calorie_coeffs":"calories per serving, indexed by foods","protein_requirement":"minimum protein","carb_requirement":"minimum carbohydrates","calorie_requirement":"minimum calories"},"variables":{"servings[food]":"nonnegative continuous"},"constraints":["sum(protein_coeffs[food]*servings[food] for food in foods) >= protein_requirement","sum(carb_coeffs[food]*servings[food] for food in foods) >= carb_requirement","sum(calorie_coeffs[food]*servings[food] for food in foods) >= calorie_requirement"],"objective":"minimize sum(costs[food]*servings[food] for food in foods)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Coefficient inputs accept food-name mappings or sequences in food order."""
    foods = ("Eggs", "Chicken", "Tofu", "Salmon", "Brown Rice", "Spinach")

    def indexed(values):
        if isinstance(values, Mapping):
            return {food: values[food] for food in foods}
        if len(values) != len(foods):
            raise ValueError("Each coefficient sequence must contain six values.")
        return {food: values[position] for position, food in enumerate(foods)}

    costs = indexed(params["costs"])
    protein_coeffs = indexed(params["protein_coeffs"])
    carb_coeffs = indexed(params["carb_coeffs"])
    calorie_coeffs = indexed(params["calorie_coeffs"])
    protein_requirement = params["protein_requirement"]
    carb_requirement = params["carb_requirement"]
    calorie_requirement = params["calorie_requirement"]

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.costs = pyo.Param(model.foods, initialize=costs)
    model.protein_coeffs = pyo.Param(model.foods, initialize=protein_coeffs)
    model.carb_coeffs = pyo.Param(model.foods, initialize=carb_coeffs)
    model.calorie_coeffs = pyo.Param(model.foods, initialize=calorie_coeffs)
    model.protein_requirement = pyo.Param(initialize=protein_requirement)
    model.carb_requirement = pyo.Param(initialize=carb_requirement)
    model.calorie_requirement = pyo.Param(initialize=calorie_requirement)

    model.servings = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein_coeffs[food] * model.servings[food]
            for food in model.foods
        ) >= model.protein_requirement
    )
    model.carb_minimum = pyo.Constraint(
        expr=sum(
            model.carb_coeffs[food] * model.servings[food]
            for food in model.foods
        ) >= model.carb_requirement
    )
    model.calorie_minimum = pyo.Constraint(
        expr=sum(
            model.calorie_coeffs[food] * model.servings[food]
            for food in model.foods
        ) >= model.calorie_requirement
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.costs[food] * model.servings[food]
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
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}