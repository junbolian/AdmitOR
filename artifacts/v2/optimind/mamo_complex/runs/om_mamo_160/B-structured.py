# IR: {"sets":{"foods":["Beef","Pasta","Broccoli","Chicken","Apple","Pork","Lentils","Eggs","Cheese"]},"params":{"cost":"cost[foods] from params","protein":"protein[foods] from params","carbs":"carbs[foods] from params","calories":"calories[foods] from params","protein_req":"scalar from params","carb_req":"scalar from params","calorie_req":"scalar from params"},"variables":{"portions[foods]":"nonnegative integer"},"constraints":["sum(protein[f]*portions[f] for f in foods) >= protein_req","sum(carbs[f]*portions[f] for f in foods) >= carb_req","sum(calories[f]*portions[f] for f in foods) >= calorie_req"],"objective":"minimize sum(cost[f]*portions[f] for f in foods)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept food data as mappings keyed by food name or sequences in IR order."""
    foods = (
        "Beef",
        "Pasta",
        "Broccoli",
        "Chicken",
        "Apple",
        "Pork",
        "Lentils",
        "Eggs",
        "Cheese",
    )

    def food_values(values):
        if isinstance(values, Mapping):
            return {food: values[food] for food in foods}
        if len(values) != len(foods):
            raise ValueError("Each food-data sequence must contain nine entries.")
        return {food: values[position] for position, food in enumerate(foods)}

    cost = food_values(params["cost"])
    protein = food_values(params["protein"])
    carbs = food_values(params["carbs"])
    calories = food_values(params["calories"])
    protein_req = params["protein_req"]
    carb_req = params["carb_req"]
    calorie_req = params["calorie_req"]

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.cost = pyo.Param(model.foods, initialize=cost)
    model.protein = pyo.Param(model.foods, initialize=protein)
    model.carbs = pyo.Param(model.foods, initialize=carbs)
    model.calories = pyo.Param(model.foods, initialize=calories)
    model.protein_req = pyo.Param(initialize=protein_req)
    model.carb_req = pyo.Param(initialize=carb_req)
    model.calorie_req = pyo.Param(initialize=calorie_req)

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
        ) >= model.calorie_req
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
    except RuntimeError as exc:
        # APPsi raises this when its default solution loading finds no solution.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}