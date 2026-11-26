# IR: {"sets":{"foods":["chicken","rice","beans","broccoli","fruit"]},"params":{"protein[food]":"params['protein_'+food]","carbs[food]":"params['carbs_'+food]","calories[food]":"params['calories_'+food]","cost[food]":"params['cost_'+food]","min_protein":"params['min_protein']","min_carbs":"params['min_carbs']","min_calories":"params['min_calories']"},"variables":{"portions[food]":{"type":"nonnegative_integer"}},"constraints":["sum(protein[food]*portions[food] for food in foods) >= min_protein","sum(carbs[food]*portions[food] for food in foods) >= min_carbs","sum(calories[food]*portions[food] for food in foods) >= min_calories"],"objective":{"sense":"minimize","expression":"sum(cost[food]*portions[food] for food in foods)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.foods = pyo.Set(
        initialize=["chicken", "rice", "beans", "broccoli", "fruit"],
        ordered=True,
    )

    model.protein = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["protein_chicken"],
            "rice": params["protein_rice"],
            "beans": params["protein_beans"],
            "broccoli": params["protein_broccoli"],
            "fruit": params["protein_fruit"],
        },
    )
    model.carbs = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["carbs_chicken"],
            "rice": params["carbs_rice"],
            "beans": params["carbs_beans"],
            "broccoli": params["carbs_broccoli"],
            "fruit": params["carbs_fruit"],
        },
    )
    model.calories = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["calories_chicken"],
            "rice": params["calories_rice"],
            "beans": params["calories_beans"],
            "broccoli": params["calories_broccoli"],
            "fruit": params["calories_fruit"],
        },
    )
    model.cost = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["cost_chicken"],
            "rice": params["cost_rice"],
            "beans": params["cost_beans"],
            "broccoli": params["cost_broccoli"],
            "fruit": params["cost_fruit"],
        },
    )

    model.min_protein = pyo.Param(initialize=params["min_protein"])
    model.min_carbs = pyo.Param(initialize=params["min_carbs"])
    model.min_calories = pyo.Param(initialize=params["min_calories"])

    model.portions = pyo.Var(model.foods, domain=pyo.NonNegativeIntegers)

    model.protein_requirement = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.portions[food]
            for food in model.foods
        ) >= model.min_protein
    )
    model.carbs_requirement = pyo.Constraint(
        expr=sum(
            model.carbs[food] * model.portions[food]
            for food in model.foods
        ) >= model.min_carbs
    )
    model.calories_requirement = pyo.Constraint(
        expr=sum(
            model.calories[food] * model.portions[food]
            for food in model.foods
        ) >= model.min_calories
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
    except RuntimeError:
        # If no solution was loaded, objective evaluation below will fail.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}