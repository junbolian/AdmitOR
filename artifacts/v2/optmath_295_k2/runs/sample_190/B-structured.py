# IR: {"sets":{"foods":"0..24","nutrients":"0..6"},"params":{"cost":"real[foods]","nutrient_min":"real[nutrients]","nutrient_max":"real[nutrients]","food_max_purchase":"real scalar","nutrient_contribution":"real[nutrients,foods]"},"variables":{"Buy":"continuous nonnegative[foods]"},"constraints":["Buy[j] <= food_max_purchase for each food j","sum(nutrient_contribution[i,j]*Buy[j] for j in foods) >= nutrient_min[i] for each nutrient i","sum(nutrient_contribution[i,j]*Buy[j] for j in foods) <= nutrient_max[i] for each nutrient i"],"objective":"minimize sum(cost[j]*Buy[j] for j in foods)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    nutrient_min = params["nutrient_min"]
    nutrient_max = params["nutrient_max"]
    food_max_purchase = params["food_max_purchase"]
    nutrient_contribution = params["nutrient_contribution"]

    model = pyo.ConcreteModel()
    model.foods = pyo.RangeSet(0, 24)
    model.nutrients = pyo.RangeSet(0, 6)

    model.food_cost = pyo.Param(
        model.foods,
        initialize={food: cost[food] for food in model.foods},
        within=pyo.Reals,
    )
    model.nutrient_lower = pyo.Param(
        model.nutrients,
        initialize={
            nutrient: nutrient_min[nutrient]
            for nutrient in model.nutrients
        },
        within=pyo.Reals,
    )
    model.nutrient_upper = pyo.Param(
        model.nutrients,
        initialize={
            nutrient: nutrient_max[nutrient]
            for nutrient in model.nutrients
        },
        within=pyo.Reals,
    )
    model.purchase_limit = pyo.Param(
        initialize=food_max_purchase,
        within=pyo.Reals,
    )
    model.contribution = pyo.Param(
        model.nutrients,
        model.foods,
        initialize={
            (nutrient, food): nutrient_contribution[nutrient][food]
            for nutrient in model.nutrients
            for food in model.foods
        },
        within=pyo.Reals,
    )

    model.Buy = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    def purchase_limit_rule(diet, food):
        return diet.Buy[food] <= diet.purchase_limit

    model.purchase_bounds = pyo.Constraint(
        model.foods, rule=purchase_limit_rule
    )

    def nutrient_minimum_rule(diet, nutrient):
        return sum(
            diet.contribution[nutrient, food] * diet.Buy[food]
            for food in diet.foods
        ) >= diet.nutrient_lower[nutrient]

    model.nutrient_minimum = pyo.Constraint(
        model.nutrients, rule=nutrient_minimum_rule
    )

    def nutrient_maximum_rule(diet, nutrient):
        return sum(
            diet.contribution[nutrient, food] * diet.Buy[food]
            for food in diet.foods
        ) <= diet.nutrient_upper[nutrient]

    model.nutrient_maximum = pyo.Constraint(
        model.nutrients, rule=nutrient_maximum_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.food_cost[food] * model.Buy[food]
            for food in model.foods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when its default solution loading finds no
        # feasible solution. Let unrelated runtime errors propagate.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}