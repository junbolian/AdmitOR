# IR: {"sets":{"foods":["Food_1","Food_2","Food_3","Food_4","Food_5"]},"params":{"cost":"cost[foods]","protein":"protein[foods]","carbs":"carbs[foods]","calories":"calories[foods]","protein_target":"scalar","carb_target":"scalar","calorie_target":"scalar"},"variables":{"quantity[foods]":"continuous, nonnegative"},"constraints":["sum(protein[f]*quantity[f] for f in foods) >= protein_target","sum(carbs[f]*quantity[f] for f in foods) >= carb_target","sum(calories[f]*quantity[f] for f in foods) >= calorie_target"],"objective":"minimize sum(cost[f]*quantity[f] for f in foods)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Nutrient and cost inputs may be sequences in Food_1 through Food_5
    order or mappings keyed by those food names. Quantities are continuous.
    """
    foods = tuple(f"Food_{food_number}" for food_number in range(1, 6))

    def food_values(values):
        if isinstance(values, Mapping):
            return {food: values[food] for food in foods}
        if len(values) != len(foods):
            raise ValueError("Each food parameter must contain five values.")
        return {food: values[position] for position, food in enumerate(foods)}

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.cost = pyo.Param(
        model.foods, initialize=food_values(params["cost"])
    )
    model.protein = pyo.Param(
        model.foods, initialize=food_values(params["protein"])
    )
    model.carbs = pyo.Param(
        model.foods, initialize=food_values(params["carbs"])
    )
    model.calories = pyo.Param(
        model.foods, initialize=food_values(params["calories"])
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
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}