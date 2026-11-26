# IR: {"sets":{"FOODS":"keys of cost if a mapping; otherwise indices 0..7"},"params":["cost[i]","protein[i]","carbs[i]","calories[i]","protein_requirement","carb_requirement","calorie_requirement"],"variables":{"portions[i]":"nonnegative integer"},"constraints":["sum(protein[i]*portions[i] for i in FOODS) >= protein_requirement","sum(carbs[i]*portions[i] for i in FOODS) >= carb_requirement","sum(calories[i]*portions[i] for i in FOODS) >= calorie_requirement"],"objective":"minimize sum(cost[i]*portions[i] for i in FOODS)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept nutrient/cost sequences or mappings sharing the same food keys."""
    cost = params["cost"]
    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    protein_requirement = params["protein_requirement"]
    carb_requirement = params["carb_requirement"]
    calorie_requirement = params["calorie_requirement"]

    food_indices = list(cost.keys()) if isinstance(cost, Mapping) else list(range(8))

    model = pyo.ConcreteModel()
    model.FOODS = pyo.Set(initialize=food_indices, ordered=True)

    model.cost = pyo.Param(
        model.FOODS, initialize={i: cost[i] for i in food_indices}
    )
    model.protein = pyo.Param(
        model.FOODS, initialize={i: protein[i] for i in food_indices}
    )
    model.carbs = pyo.Param(
        model.FOODS, initialize={i: carbs[i] for i in food_indices}
    )
    model.calories = pyo.Param(
        model.FOODS, initialize={i: calories[i] for i in food_indices}
    )
    model.protein_requirement = pyo.Param(initialize=protein_requirement)
    model.carb_requirement = pyo.Param(initialize=carb_requirement)
    model.calorie_requirement = pyo.Param(initialize=calorie_requirement)

    model.portions = pyo.Var(model.FOODS, domain=pyo.NonNegativeIntegers)

    model.protein_minimum = pyo.Constraint(
        expr=sum(model.protein[i] * model.portions[i] for i in model.FOODS)
        >= model.protein_requirement
    )
    model.carb_minimum = pyo.Constraint(
        expr=sum(model.carbs[i] * model.portions[i] for i in model.FOODS)
        >= model.carb_requirement
    )
    model.calorie_minimum = pyo.Constraint(
        expr=sum(model.calories[i] * model.portions[i] for i in model.FOODS)
        >= model.calorie_requirement
    )

    model.total_cost = pyo.Objective(
        expr=sum(model.cost[i] * model.portions[i] for i in model.FOODS),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}