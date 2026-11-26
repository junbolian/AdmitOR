# IR: {"sets":{"foods":["Chicken","Tuna","Eggs","Beef","Rice","Apples","Bread"]},"params":{"protein":"grams per portion, indexed by foods","carbs":"grams per portion, indexed by foods","calories":"calories per portion, indexed by foods","price":"dollars per portion, indexed by foods","protein_target":"minimum weekly protein","carb_target":"minimum weekly carbohydrates","calorie_target":"minimum weekly calories"},"variables":{"portions[foods]":"nonnegative integer"},"constraints":["sum(protein[f]*portions[f] for f in foods) >= protein_target","sum(carbs[f]*portions[f] for f in foods) >= carb_target","sum(calories[f]*portions[f] for f in foods) >= calorie_target"],"objective":{"sense":"minimize","expression":"sum(price[f]*portions[f] for f in foods)"}}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ("Chicken", "Tuna", "Eggs", "Beef", "Rice", "Apples", "Bread")

    # Indexed inputs may be mappings keyed by food name or sequences in foods order.
    def food_data(values):
        if isinstance(values, Mapping):
            return {food: values[food] for food in foods}
        if len(values) != len(foods):
            raise ValueError("Food coefficient sequences must contain seven entries.")
        return dict(zip(foods, values))

    protein_data = food_data(params["protein"])
    carb_data = food_data(params["carbs"])
    calorie_data = food_data(params["calories"])
    price_data = food_data(params["price"])
    protein_target = params["protein_target"]
    carb_target = params["carb_target"]
    calorie_target = params["calorie_target"]

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.protein = pyo.Param(model.foods, initialize=protein_data)
    model.carbs = pyo.Param(model.foods, initialize=carb_data)
    model.calories = pyo.Param(model.foods, initialize=calorie_data)
    model.price = pyo.Param(model.foods, initialize=price_data)
    model.protein_target = pyo.Param(initialize=protein_target)
    model.carb_target = pyo.Param(initialize=carb_target)
    model.calorie_target = pyo.Param(initialize=calorie_target)

    model.portions = pyo.Var(model.foods, domain=pyo.NonNegativeIntegers)

    model.protein_requirement = pyo.Constraint(
        expr=sum(model.protein[food] * model.portions[food] for food in model.foods)
        >= model.protein_target
    )
    model.carb_requirement = pyo.Constraint(
        expr=sum(model.carbs[food] * model.portions[food] for food in model.foods)
        >= model.carb_target
    )
    model.calorie_requirement = pyo.Constraint(
        expr=sum(model.calories[food] * model.portions[food] for food in model.foods)
        >= model.calorie_target
    )

    model.total_cost = pyo.Objective(
        expr=sum(model.price[food] * model.portions[food] for food in model.foods),
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