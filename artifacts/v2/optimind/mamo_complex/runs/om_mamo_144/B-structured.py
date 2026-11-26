# IR: {"sets":{"foods":[1,2,3,4]},"params":{"protein_content":"grams/serving[foods]","carb_content":"grams/serving[foods]","calorie_content":"calories/serving[foods]","food_cost":"dollars/serving[foods]","protein_requirement":"minimum grams","carb_requirement":"minimum grams","calorie_requirement":"minimum calories"},"variables":{"servings[foods]":"nonnegative integer"},"constraints":["sum(protein_content[i]*servings[i]) >= protein_requirement","sum(carb_content[i]*servings[i]) >= carb_requirement","sum(calorie_content[i]*servings[i]) >= calorie_requirement"],"objective":"minimize sum(food_cost[i]*servings[i])"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Nutrient and cost vectors are sequences ordered by foods 1–4.

    Integer servings follow the problem's final requirement.
    """
    model = pyo.ConcreteModel()
    model.foods = pyo.RangeSet(1, 4)

    model.protein_content = pyo.Param(
        model.foods,
        initialize={
            food: params["protein_content"][food - 1]
            for food in model.foods
        },
    )
    model.carb_content = pyo.Param(
        model.foods,
        initialize={
            food: params["carb_content"][food - 1]
            for food in model.foods
        },
    )
    model.calorie_content = pyo.Param(
        model.foods,
        initialize={
            food: params["calorie_content"][food - 1]
            for food in model.foods
        },
    )
    model.food_cost = pyo.Param(
        model.foods,
        initialize={
            food: params["food_cost"][food - 1]
            for food in model.foods
        },
    )

    model.protein_requirement = pyo.Param(
        initialize=params["protein_requirement"]
    )
    model.carb_requirement = pyo.Param(
        initialize=params["carb_requirement"]
    )
    model.calorie_requirement = pyo.Param(
        initialize=params["calorie_requirement"]
    )

    model.servings = pyo.Var(
        model.foods, domain=pyo.NonNegativeIntegers
    )

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein_content[food] * model.servings[food]
            for food in model.foods
        ) >= model.protein_requirement
    )
    model.carb_minimum = pyo.Constraint(
        expr=sum(
            model.carb_content[food] * model.servings[food]
            for food in model.foods
        ) >= model.carb_requirement
    )
    model.calorie_minimum = pyo.Constraint(
        expr=sum(
            model.calorie_content[food] * model.servings[food]
            for food in model.foods
        ) >= model.calorie_requirement
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.food_cost[food] * model.servings[food]
            for food in model.foods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPSI raises this when no feasible solution can be loaded.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}