# IR: {"sets":{"foods":["chicken","tofu","rice","avocado"]},"params":["protein_chicken","carbs_chicken","calories_chicken","cost_chicken","protein_tofu","carbs_tofu","calories_tofu","cost_tofu","protein_rice","carbs_rice","calories_rice","cost_rice","protein_avocado","carbs_avocado","calories_avocado","cost_avocado","protein_min","carbs_min","calories_min"],"variables":{"servings[foods]":{"type":"continuous","domain":"nonnegative"}},"constraints":["sum(protein[food]*servings[food] for food in foods) >= protein_min","sum(carbs[food]*servings[food] for food in foods) >= carbs_min","sum(calories[food]*servings[food] for food in foods) >= calories_min"],"objective":{"sense":"minimize","expression":"sum(cost[food]*servings[food] for food in foods)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.foods = pyo.Set(
        initialize=["chicken", "tofu", "rice", "avocado"],
        ordered=True,
    )

    model.protein = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["protein_chicken"],
            "tofu": params["protein_tofu"],
            "rice": params["protein_rice"],
            "avocado": params["protein_avocado"],
        },
    )
    model.carbs = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["carbs_chicken"],
            "tofu": params["carbs_tofu"],
            "rice": params["carbs_rice"],
            "avocado": params["carbs_avocado"],
        },
    )
    model.calories = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["calories_chicken"],
            "tofu": params["calories_tofu"],
            "rice": params["calories_rice"],
            "avocado": params["calories_avocado"],
        },
    )
    model.cost = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["cost_chicken"],
            "tofu": params["cost_tofu"],
            "rice": params["cost_rice"],
            "avocado": params["cost_avocado"],
        },
    )

    model.protein_min = pyo.Param(initialize=params["protein_min"])
    model.carbs_min = pyo.Param(initialize=params["carbs_min"])
    model.calories_min = pyo.Param(initialize=params["calories_min"])

    model.servings = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_requirement = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.servings[food]
            for food in model.foods
        ) >= model.protein_min
    )
    model.carbs_requirement = pyo.Constraint(
        expr=sum(
            model.carbs[food] * model.servings[food]
            for food in model.foods
        ) >= model.carbs_min
    )
    model.calories_requirement = pyo.Constraint(
        expr=sum(
            model.calories[food] * model.servings[food]
            for food in model.foods
        ) >= model.calories_min
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[food] * model.servings[food]
            for food in model.foods
        ),
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