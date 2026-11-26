# IR: {"sets":{"foods":["chicken","rice","beans","avocado"]},"params":["protein_goal","carb_goal","calorie_goal","cost_chicken","cost_rice","cost_beans","cost_avocado","protein_chicken","protein_rice","protein_beans","protein_avocado","carb_chicken","carb_rice","carb_beans","carb_avocado","cal_chicken","cal_rice","cal_beans","cal_avocado"],"variables":{"servings[foods]":"nonnegative integer"},"constraints":["sum(protein[f]*servings[f] for f in foods) >= protein_goal","sum(carb[f]*servings[f] for f in foods) >= carb_goal","sum(cal[f]*servings[f] for f in foods) >= calorie_goal"],"objective":"minimize sum(cost[f]*servings[f] for f in foods)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.foods = pyo.Set(
        initialize=["chicken", "rice", "beans", "avocado"],
        ordered=True,
    )

    model.protein_goal = pyo.Param(initialize=params["protein_goal"])
    model.carb_goal = pyo.Param(initialize=params["carb_goal"])
    model.calorie_goal = pyo.Param(initialize=params["calorie_goal"])

    model.cost = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["cost_chicken"],
            "rice": params["cost_rice"],
            "beans": params["cost_beans"],
            "avocado": params["cost_avocado"],
        },
    )
    model.protein = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["protein_chicken"],
            "rice": params["protein_rice"],
            "beans": params["protein_beans"],
            "avocado": params["protein_avocado"],
        },
    )
    model.carb = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["carb_chicken"],
            "rice": params["carb_rice"],
            "beans": params["carb_beans"],
            "avocado": params["carb_avocado"],
        },
    )
    model.cal = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["cal_chicken"],
            "rice": params["cal_rice"],
            "beans": params["cal_beans"],
            "avocado": params["cal_avocado"],
        },
    )

    model.servings = pyo.Var(model.foods, domain=pyo.NonNegativeIntegers)

    model.protein_requirement = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.servings[food]
            for food in model.foods
        ) >= model.protein_goal
    )
    model.carb_requirement = pyo.Constraint(
        expr=sum(
            model.carb[food] * model.servings[food]
            for food in model.foods
        ) >= model.carb_goal
    )
    model.calorie_requirement = pyo.Constraint(
        expr=sum(
            model.cal[food] * model.servings[food]
            for food in model.foods
        ) >= model.calorie_goal
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
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}