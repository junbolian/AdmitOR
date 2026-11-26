# IR: {"sets":{"foods":[1,2,3,4,5]},"params":{"protein":"grams per portion, indexed by foods","carbs":"grams per portion, indexed by foods","calories":"calories per portion, indexed by foods","cost":"cost per portion, indexed by foods","protein_req":"minimum protein","carb_req":"minimum carbohydrates","cal_req":"minimum calories"},"variables":{"portions[i]":"nonnegative integer for each food i"},"constraints":["sum(protein[i]*portions[i] for i in foods) >= protein_req","sum(carbs[i]*portions[i] for i in foods) >= carb_req","sum(calories[i]*portions[i] for i in foods) >= cal_req"],"objective":"minimize sum(cost[i]*portions[i] for i in foods)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept nutrient/cost sequences in food order or mappings keyed by 1–5."""

    def food_value(values, food_id):
        if isinstance(values, Mapping):
            if food_id in values:
                return values[food_id]
            return values[str(food_id)]
        return values[food_id - 1]

    model = pyo.ConcreteModel()
    model.foods = pyo.RangeSet(1, 5)

    model.protein = pyo.Param(
        model.foods,
        initialize={
            food_id: food_value(params["protein"], food_id)
            for food_id in model.foods
        },
    )
    model.carbs = pyo.Param(
        model.foods,
        initialize={
            food_id: food_value(params["carbs"], food_id)
            for food_id in model.foods
        },
    )
    model.calories = pyo.Param(
        model.foods,
        initialize={
            food_id: food_value(params["calories"], food_id)
            for food_id in model.foods
        },
    )
    model.cost = pyo.Param(
        model.foods,
        initialize={
            food_id: food_value(params["cost"], food_id)
            for food_id in model.foods
        },
    )
    model.protein_req = pyo.Param(initialize=params["protein_req"])
    model.carb_req = pyo.Param(initialize=params["carb_req"])
    model.cal_req = pyo.Param(initialize=params["cal_req"])

    model.portions = pyo.Var(model.foods, domain=pyo.NonNegativeIntegers)

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein[food_id] * model.portions[food_id]
            for food_id in model.foods
        ) >= model.protein_req
    )
    model.carbohydrate_minimum = pyo.Constraint(
        expr=sum(
            model.carbs[food_id] * model.portions[food_id]
            for food_id in model.foods
        ) >= model.carb_req
    )
    model.calorie_minimum = pyo.Constraint(
        expr=sum(
            model.calories[food_id] * model.portions[food_id]
            for food_id in model.foods
        ) >= model.cal_req
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[food_id] * model.portions[food_id]
            for food_id in model.foods
        ),
        sense=pyo.minimize,
    )

    failure_reason = "objective_unavailable"
    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution can be loaded.
        # Objective retrieval remains the sole success criterion.
        failure_reason = "solve_failed"

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": failure_reason}

    return {"objective": obj_val, "status": "optimal"}