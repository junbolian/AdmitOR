# IR: {"sets":{"foods":["lentils","rice","chicken","beef","tofu"]},"params":["cost_lentils","cost_rice","cost_chicken","cost_beef","cost_tofu","protein_lentils","protein_rice","protein_chicken","protein_beef","protein_tofu","carbs_lentils","carbs_rice","carbs_chicken","carbs_beef","carbs_tofu","calories_lentils","calories_rice","calories_chicken","calories_beef","calories_tofu","protein_req","carbs_req","calorie_req"],"variables":{"quantity[food]":"nonnegative continuous"},"constraints":["sum(protein[food]*quantity[food] for food in foods) >= protein_req","sum(carbs[food]*quantity[food] for food in foods) >= carbs_req","sum(calories[food]*quantity[food] for food in foods) >= calorie_req"],"objective":{"sense":"minimize","expression":"sum(cost[food]*quantity[food] for food in foods)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.foods = pyo.Set(
        initialize=["lentils", "rice", "chicken", "beef", "tofu"],
        ordered=True,
    )

    model.cost = pyo.Param(
        model.foods,
        initialize={
            "lentils": params["cost_lentils"],
            "rice": params["cost_rice"],
            "chicken": params["cost_chicken"],
            "beef": params["cost_beef"],
            "tofu": params["cost_tofu"],
        },
    )
    model.protein = pyo.Param(
        model.foods,
        initialize={
            "lentils": params["protein_lentils"],
            "rice": params["protein_rice"],
            "chicken": params["protein_chicken"],
            "beef": params["protein_beef"],
            "tofu": params["protein_tofu"],
        },
    )
    model.carbs = pyo.Param(
        model.foods,
        initialize={
            "lentils": params["carbs_lentils"],
            "rice": params["carbs_rice"],
            "chicken": params["carbs_chicken"],
            "beef": params["carbs_beef"],
            "tofu": params["carbs_tofu"],
        },
    )
    model.calories = pyo.Param(
        model.foods,
        initialize={
            "lentils": params["calories_lentils"],
            "rice": params["calories_rice"],
            "chicken": params["calories_chicken"],
            "beef": params["calories_beef"],
            "tofu": params["calories_tofu"],
        },
    )

    model.protein_req = pyo.Param(initialize=params["protein_req"])
    model.carbs_req = pyo.Param(initialize=params["carbs_req"])
    model.calorie_req = pyo.Param(initialize=params["calorie_req"])

    model.quantity = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.quantity[food]
            for food in model.foods
        ) >= model.protein_req
    )
    model.carbs_minimum = pyo.Constraint(
        expr=sum(
            model.carbs[food] * model.quantity[food]
            for food in model.foods
        ) >= model.carbs_req
    )
    model.calorie_minimum = pyo.Constraint(
        expr=sum(
            model.calories[food] * model.quantity[food]
            for food in model.foods
        ) >= model.calorie_req
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[food] * model.quantity[food]
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