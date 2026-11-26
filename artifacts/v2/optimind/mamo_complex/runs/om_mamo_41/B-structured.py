# IR: {"sets":{"foods":["chicken","rice","eggs","broccoli","lentils","apples"]},"params":{"protein[food]":"params['protein_' + food]","carb[food]":"params['carb_' + food]","calories[food]":"params['cal_' + food]","cost[food]":"params['cost_' + food]","req_protein":"params['req_protein']","req_carbs":"params['req_carbs']","req_calories":"params['req_calories']"},"variables":{"portions[food]":{"type":"integer","lower_bound":0}},"constraints":["sum(protein[food]*portions[food] for food in foods) >= req_protein","sum(carb[food]*portions[food] for food in foods) >= req_carbs","sum(calories[food]*portions[food] for food in foods) >= req_calories"],"objective":{"sense":"minimize","expression":"sum(cost[food]*portions[food] for food in foods)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ("chicken", "rice", "eggs", "broccoli", "lentils", "apples")

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.protein = pyo.Param(
        model.foods,
        initialize={food: params["protein_" + food] for food in foods},
    )
    model.carb = pyo.Param(
        model.foods,
        initialize={food: params["carb_" + food] for food in foods},
    )
    model.calories = pyo.Param(
        model.foods,
        initialize={food: params["cal_" + food] for food in foods},
    )
    model.cost = pyo.Param(
        model.foods,
        initialize={food: params["cost_" + food] for food in foods},
    )
    model.req_protein = pyo.Param(initialize=params["req_protein"])
    model.req_carbs = pyo.Param(initialize=params["req_carbs"])
    model.req_calories = pyo.Param(initialize=params["req_calories"])

    model.portions = pyo.Var(model.foods, domain=pyo.NonNegativeIntegers)

    model.protein_requirement = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.portions[food]
            for food in model.foods
        ) >= model.req_protein
    )
    model.carbohydrate_requirement = pyo.Constraint(
        expr=sum(
            model.carb[food] * model.portions[food]
            for food in model.foods
        ) >= model.req_carbs
    )
    model.calorie_requirement = pyo.Constraint(
        expr=sum(
            model.calories[food] * model.portions[food]
            for food in model.foods
        ) >= model.req_calories
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
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}