# IR: {"sets":{"foods":["chicken","rice","lentils","apples","eggs","broccoli"]},"params":["protein_chicken","carb_chicken","cal_chicken","cost_chicken","protein_rice","carb_rice","cal_rice","cost_rice","protein_lentils","carb_lentils","cal_lentils","cost_lentils","protein_apples","carb_apples","cal_apples","cost_apples","protein_eggs","carb_eggs","cal_eggs","cost_eggs","protein_broccoli","carb_broccoli","cal_broccoli","cost_broccoli","req_protein","req_carbs","req_calories"],"variables":{"servings[food]":"NonNegativeReals"},"constraints":["sum(protein[food]*servings[food] for food in foods) >= req_protein","sum(carb[food]*servings[food] for food in foods) >= req_carbs","sum(cal[food]*servings[food] for food in foods) >= req_calories"],"objective":"minimize sum(cost[food]*servings[food] for food in foods)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.foods = pyo.Set(
        initialize=["chicken", "rice", "lentils", "apples", "eggs", "broccoli"],
        ordered=True,
    )

    model.protein = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["protein_chicken"],
            "rice": params["protein_rice"],
            "lentils": params["protein_lentils"],
            "apples": params["protein_apples"],
            "eggs": params["protein_eggs"],
            "broccoli": params["protein_broccoli"],
        },
    )
    model.carb = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["carb_chicken"],
            "rice": params["carb_rice"],
            "lentils": params["carb_lentils"],
            "apples": params["carb_apples"],
            "eggs": params["carb_eggs"],
            "broccoli": params["carb_broccoli"],
        },
    )
    model.cal = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["cal_chicken"],
            "rice": params["cal_rice"],
            "lentils": params["cal_lentils"],
            "apples": params["cal_apples"],
            "eggs": params["cal_eggs"],
            "broccoli": params["cal_broccoli"],
        },
    )
    model.cost = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["cost_chicken"],
            "rice": params["cost_rice"],
            "lentils": params["cost_lentils"],
            "apples": params["cost_apples"],
            "eggs": params["cost_eggs"],
            "broccoli": params["cost_broccoli"],
        },
    )
    model.req_protein = pyo.Param(initialize=params["req_protein"])
    model.req_carbs = pyo.Param(initialize=params["req_carbs"])
    model.req_calories = pyo.Param(initialize=params["req_calories"])

    model.servings = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_requirement = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.servings[food] for food in model.foods
        ) >= model.req_protein
    )
    model.carbohydrate_requirement = pyo.Constraint(
        expr=sum(
            model.carb[food] * model.servings[food] for food in model.foods
        ) >= model.req_carbs
    )
    model.calorie_requirement = pyo.Constraint(
        expr=sum(
            model.cal[food] * model.servings[food] for food in model.foods
        ) >= model.req_calories
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[food] * model.servings[food] for food in model.foods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}