# IR: {"sets":{"foods":"0..24","nutrients":"0..6"},"params":{"food_cost":"real[foods]","max_buy_per_food":"nonnegative real scalar","nutrient_min":"real[nutrients]","nutrient_max":"real[nutrients]","nutrient_coefficients":"real[nutrients,foods]"},"variables":{"Buy":"continuous nonnegative real[foods], upper bound max_buy_per_food"},"constraints":["For each nutrient n: sum(nutrient_coefficients[n,f]*Buy[f] for f in foods) >= nutrient_min[n]","For each nutrient n: sum(nutrient_coefficients[n,f]*Buy[f] for f in foods) <= nutrient_max[n]"],"objective":"minimize sum(food_cost[f]*Buy[f] for f in foods)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Inputs use zero-based sequences; coefficients are nutrient-major."""
    food_cost = params["food_cost"]
    max_buy_per_food = params["max_buy_per_food"]
    nutrient_min = params["nutrient_min"]
    nutrient_max = params["nutrient_max"]
    nutrient_coefficients = params["nutrient_coefficients"]

    model = pyo.ConcreteModel()
    model.foods = pyo.RangeSet(0, 24)
    model.nutrients = pyo.RangeSet(0, 6)

    model.food_cost = pyo.Param(
        model.foods,
        initialize=lambda mdl, food: food_cost[food],
        within=pyo.Reals,
    )
    model.max_buy_per_food = pyo.Param(
        initialize=max_buy_per_food,
        within=pyo.NonNegativeReals,
    )
    model.nutrient_min = pyo.Param(
        model.nutrients,
        initialize=lambda mdl, nutrient: nutrient_min[nutrient],
        within=pyo.Reals,
    )
    model.nutrient_max = pyo.Param(
        model.nutrients,
        initialize=lambda mdl, nutrient: nutrient_max[nutrient],
        within=pyo.Reals,
    )
    model.nutrient_coefficients = pyo.Param(
        model.nutrients,
        model.foods,
        initialize=lambda mdl, nutrient, food: (
            nutrient_coefficients[nutrient][food]
        ),
        within=pyo.Reals,
    )

    model.Buy = pyo.Var(
        model.foods,
        domain=pyo.NonNegativeReals,
        bounds=lambda mdl, food: (0, mdl.max_buy_per_food),
    )

    def nutrient_total(mdl, nutrient):
        return sum(
            mdl.nutrient_coefficients[nutrient, food] * mdl.Buy[food]
            for food in mdl.foods
        )

    model.nutrient_lower_bounds = pyo.Constraint(
        model.nutrients,
        rule=lambda mdl, nutrient: (
            nutrient_total(mdl, nutrient) >= mdl.nutrient_min[nutrient]
        ),
    )
    model.nutrient_upper_bounds = pyo.Constraint(
        model.nutrients,
        rule=lambda mdl, nutrient: (
            nutrient_total(mdl, nutrient) <= mdl.nutrient_max[nutrient]
        ),
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.food_cost[food] * model.Buy[food]
            for food in model.foods
        ),
        sense=pyo.minimize,
    )

    # APPsi may raise when it cannot load a feasible solution.
    # Objective retrieval alone determines success.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}