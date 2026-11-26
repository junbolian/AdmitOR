# IR: {"sets":{"foods":["Food_1","Food_2","Food_3","Food_4","Food_5","Food_6","Food_7","Food_8"]},"params":{"cost":"per-food costs","protein":"per-food protein","carbs":"per-food carbohydrates","calories":"per-food calories","protein_req":"minimum protein","carb_req":"minimum carbohydrates","cal_req":"minimum calories"},"variables":{"portions[food]":"nonnegative integer"},"constraints":["sum(protein[food]*portions[food]) >= protein_req","sum(carbs[food]*portions[food]) >= carb_req","sum(calories[food]*portions[food]) >= cal_req"],"objective":"minimize sum(cost[food]*portions[food])"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept food data as ordered sequences or mappings keyed by Food_1,...,Food_8."""
    foods = tuple(f"Food_{idx}" for idx in range(1, 9))

    def food_data(values):
        if isinstance(values, Mapping):
            return {food: values[food] for food in foods}
        if len(values) != len(foods):
            raise ValueError("Each food parameter must contain eight values.")
        return {food: values[idx] for idx, food in enumerate(foods)}

    cost_data = food_data(params["cost"])
    protein_data = food_data(params["protein"])
    carb_data = food_data(params["carbs"])
    calorie_data = food_data(params["calories"])
    protein_requirement = params["protein_req"]
    carb_requirement = params["carb_req"]
    calorie_requirement = params["cal_req"]

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.cost = pyo.Param(model.foods, initialize=cost_data)
    model.protein = pyo.Param(model.foods, initialize=protein_data)
    model.carbs = pyo.Param(model.foods, initialize=carb_data)
    model.calories = pyo.Param(model.foods, initialize=calorie_data)
    model.protein_req = pyo.Param(initialize=protein_requirement)
    model.carb_req = pyo.Param(initialize=carb_requirement)
    model.cal_req = pyo.Param(initialize=calorie_requirement)

    model.portions = pyo.Var(model.foods, domain=pyo.NonNegativeIntegers)

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.portions[food]
            for food in model.foods
        ) >= model.protein_req
    )
    model.carb_minimum = pyo.Constraint(
        expr=sum(
            model.carbs[food] * model.portions[food]
            for food in model.foods
        ) >= model.carb_req
    )
    model.calorie_minimum = pyo.Constraint(
        expr=sum(
            model.calories[food] * model.portions[food]
            for food in model.foods
        ) >= model.cal_req
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
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}