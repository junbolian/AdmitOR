# IR: {"sets":{"foods":"0..24","nutrients":"0..6"},"params":{"cost":"real[foods]","nutrient_min":"real[nutrients]","nutrient_max":"real[nutrients]","food_max_purchase":"real scalar","nutrient_contribution":"real[nutrients,foods]"},"variables":{"Buy":"continuous nonnegative[foods]"},"constraints":["Buy[f] <= food_max_purchase for each food f","sum(nutrient_contribution[n,f]*Buy[f] for f in foods) >= nutrient_min[n] for each nutrient n","sum(nutrient_contribution[n,f]*Buy[f] for f in foods) <= nutrient_max[n] for each nutrient n"],"objective":"minimize sum(cost[f]*Buy[f] for f in foods)"}

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

    model.cost = pyo.Param(
        model.foods,
        initialize={food: cost[food] for food in model.foods},
        within=pyo.Reals,
    )
    model.nutrient_min = pyo.Param(
        model.nutrients,
        initialize={
            nutrient: nutrient_min[nutrient]
            for nutrient in model.nutrients
        },
        within=pyo.Reals,
    )
    model.nutrient_max = pyo.Param(
        model.nutrients,
        initialize={
            nutrient: nutrient_max[nutrient]
            for nutrient in model.nutrients
        },
        within=pyo.Reals,
    )
    model.food_max_purchase = pyo.Param(
        initialize=food_max_purchase,
        within=pyo.Reals,
    )
    model.nutrient_contribution = pyo.Param(
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

    def purchase_limit_rule(problem, food):
        return problem.Buy[food] <= problem.food_max_purchase

    model.purchase_limit = pyo.Constraint(
        model.foods,
        rule=purchase_limit_rule,
    )

    def nutrient_lower_rule(problem, nutrient):
        return (
            pyo.quicksum(
                problem.nutrient_contribution[nutrient, food]
                * problem.Buy[food]
                for food in problem.foods
            )
            >= problem.nutrient_min[nutrient]
        )

    model.nutrient_lower = pyo.Constraint(
        model.nutrients,
        rule=nutrient_lower_rule,
    )

    def nutrient_upper_rule(problem, nutrient):
        return (
            pyo.quicksum(
                problem.nutrient_contribution[nutrient, food]
                * problem.Buy[food]
                for food in problem.foods
            )
            <= problem.nutrient_max[nutrient]
        )

    model.nutrient_upper = pyo.Constraint(
        model.nutrients,
        rule=nutrient_upper_rule,
    )

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.cost[food] * model.Buy[food]
            for food in model.foods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}