# IR: {"sets":{"foods":["chicken","cheese","rice","beans"]},"params":{"protein":["protein_chicken","protein_cheese","protein_rice","protein_beans"],"carbs":["carbs_chicken","carbs_cheese","carbs_rice","carbs_beans"],"calories":["calories_chicken","calories_cheese","calories_rice","calories_beans"],"price":["price_chicken","price_cheese","price_rice","price_beans"],"requirements":["protein_req","carbs_req","calories_req"]},"variables":{"quantity[food]":{"type":"continuous","lower_bound":0}},"constraints":["sum(protein[food]*quantity[food] for food in foods) >= protein_req","sum(carbs[food]*quantity[food] for food in foods) >= carbs_req","sum(calories[food]*quantity[food] for food in foods) >= calories_req"],"objective":{"sense":"minimize","expression":"sum(price[food]*quantity[food] for food in foods)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.foods = pyo.Set(
        initialize=("chicken", "cheese", "rice", "beans"),
        ordered=True,
    )

    model.protein = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["protein_chicken"],
            "cheese": params["protein_cheese"],
            "rice": params["protein_rice"],
            "beans": params["protein_beans"],
        },
    )
    model.carbs = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["carbs_chicken"],
            "cheese": params["carbs_cheese"],
            "rice": params["carbs_rice"],
            "beans": params["carbs_beans"],
        },
    )
    model.calories = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["calories_chicken"],
            "cheese": params["calories_cheese"],
            "rice": params["calories_rice"],
            "beans": params["calories_beans"],
        },
    )
    model.price = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["price_chicken"],
            "cheese": params["price_cheese"],
            "rice": params["price_rice"],
            "beans": params["price_beans"],
        },
    )

    model.protein_req = pyo.Param(initialize=params["protein_req"])
    model.carbs_req = pyo.Param(initialize=params["carbs_req"])
    model.calories_req = pyo.Param(initialize=params["calories_req"])

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
    model.calories_minimum = pyo.Constraint(
        expr=sum(
            model.calories[food] * model.quantity[food]
            for food in model.foods
        ) >= model.calories_req
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.price[food] * model.quantity[food]
            for food in model.foods
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