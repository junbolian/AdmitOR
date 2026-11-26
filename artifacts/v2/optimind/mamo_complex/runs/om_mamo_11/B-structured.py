# IR: {"sets":{"foods":["chicken","tofu","brown_rice","fish","lentils","quinoa","eggs","beef","beans"]},"params":{"cost[food]":"params[food + '_cost']","protein[food]":"params['protein_per_item'] in foods order or keyed by food","carbs[food]":"params['carbs_per_item'] in foods order or keyed by food","calories[food]":"params['calories_per_item'] in foods order or keyed by food","protein_req":"params['protein_req']","carbs_req":"params['carbs_req']","calories_req":"params['calories_req']"},"variables":{"portions[food]":"nonnegative integer"},"constraints":["sum(protein[food]*portions[food]) >= protein_req","sum(carbs[food]*portions[food]) >= carbs_req","sum(calories[food]*portions[food]) >= calories_req"],"objective":"minimize sum(cost[food]*portions[food])"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = (
        "chicken",
        "tofu",
        "brown_rice",
        "fish",
        "lentils",
        "quinoa",
        "eggs",
        "beef",
        "beans",
    )

    costs = {
        "chicken": params["chicken_cost"],
        "tofu": params["tofu_cost"],
        "brown_rice": params["brown_rice_cost"],
        "fish": params["fish_cost"],
        "lentils": params["lentils_cost"],
        "quinoa": params["quinoa_cost"],
        "eggs": params["eggs_cost"],
        "beef": params["beef_cost"],
        "beans": params["beans_cost"],
    }

    def nutrient_mapping(values):
        if isinstance(values, Mapping):
            return {food: values[food] for food in foods}
        if len(values) != len(foods):
            raise ValueError("Each nutrient sequence must contain nine values.")
        return {food: values[position] for position, food in enumerate(foods)}

    protein = nutrient_mapping(params["protein_per_item"])
    carbs = nutrient_mapping(params["carbs_per_item"])
    calories = nutrient_mapping(params["calories_per_item"])

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.cost = pyo.Param(model.foods, initialize=costs, within=pyo.Reals)
    model.protein = pyo.Param(model.foods, initialize=protein, within=pyo.Reals)
    model.carbs = pyo.Param(model.foods, initialize=carbs, within=pyo.Reals)
    model.calories = pyo.Param(model.foods, initialize=calories, within=pyo.Reals)

    model.protein_req = pyo.Param(
        initialize=params["protein_req"], within=pyo.Reals
    )
    model.carbs_req = pyo.Param(
        initialize=params["carbs_req"], within=pyo.Reals
    )
    model.calories_req = pyo.Param(
        initialize=params["calories_req"], within=pyo.Reals
    )

    model.portions = pyo.Var(model.foods, domain=pyo.NonNegativeIntegers)

    model.protein_requirement = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.portions[food] for food in model.foods
        ) >= model.protein_req
    )
    model.carbohydrate_requirement = pyo.Constraint(
        expr=sum(
            model.carbs[food] * model.portions[food] for food in model.foods
        ) >= model.carbs_req
    )
    model.calorie_requirement = pyo.Constraint(
        expr=sum(
            model.calories[food] * model.portions[food] for food in model.foods
        ) >= model.calories_req
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[food] * model.portions[food] for food in model.foods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution can be loaded.
        # Objective retrieval below remains the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}