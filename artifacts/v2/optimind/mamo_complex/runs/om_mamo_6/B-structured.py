# IR: {"sets":{"foods":"0..8, ordered as Chicken Breast, Tofu, Brown Rice, Salmon, Greek Yogurt, Steak, Avocado, Eggs, Quinoa"},"params":{"costs":"costs[foods]","protein":"protein[foods]","carbs":"carbs[foods]","calories":"calories[foods]","protein_target":"scalar","carb_target":"scalar","calorie_target":"scalar"},"variables":{"portions[foods]":"NonNegativeIntegers"},"constraints":["sum(protein[i]*portions[i] for i in foods) >= protein_target","sum(carbs[i]*portions[i] for i in foods) >= carb_target","sum(calories[i]*portions[i] for i in foods) >= calorie_target"],"objective":"minimize sum(costs[i]*portions[i] for i in foods)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using nine-element nutrient and cost sequences in the IR order."""
    model = pyo.ConcreteModel()
    model.foods = pyo.RangeSet(0, 8)

    model.costs = pyo.Param(
        model.foods,
        initialize={food_idx: params["costs"][food_idx] for food_idx in model.foods},
        within=pyo.Reals,
    )
    model.protein = pyo.Param(
        model.foods,
        initialize={food_idx: params["protein"][food_idx] for food_idx in model.foods},
        within=pyo.Reals,
    )
    model.carbs = pyo.Param(
        model.foods,
        initialize={food_idx: params["carbs"][food_idx] for food_idx in model.foods},
        within=pyo.Reals,
    )
    model.calories = pyo.Param(
        model.foods,
        initialize={food_idx: params["calories"][food_idx] for food_idx in model.foods},
        within=pyo.Reals,
    )
    model.protein_target = pyo.Param(
        initialize=params["protein_target"], within=pyo.Reals
    )
    model.carb_target = pyo.Param(
        initialize=params["carb_target"], within=pyo.Reals
    )
    model.calorie_target = pyo.Param(
        initialize=params["calorie_target"], within=pyo.Reals
    )

    model.portions = pyo.Var(model.foods, domain=pyo.NonNegativeIntegers)

    model.protein_requirement = pyo.Constraint(
        expr=sum(
            model.protein[food_idx] * model.portions[food_idx]
            for food_idx in model.foods
        ) >= model.protein_target
    )
    model.carb_requirement = pyo.Constraint(
        expr=sum(
            model.carbs[food_idx] * model.portions[food_idx]
            for food_idx in model.foods
        ) >= model.carb_target
    )
    model.calorie_requirement = pyo.Constraint(
        expr=sum(
            model.calories[food_idx] * model.portions[food_idx]
            for food_idx in model.foods
        ) >= model.calorie_target
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.costs[food_idx] * model.portions[food_idx]
            for food_idx in model.foods
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