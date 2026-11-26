# IR: {"sets":{"foods":["steak","eggs","pasta","chicken"]},"params":["protein_steak","protein_eggs","protein_pasta","protein_chicken","carbs_steak","carbs_eggs","carbs_pasta","carbs_chicken","calories_steak","calories_eggs","calories_pasta","calories_chicken","cost_steak","cost_eggs","cost_pasta","cost_chicken","protein_req","carbs_req","calories_req"],"variables":{"quantity[foods]":"NonNegativeReals"},"constraints":["sum(protein[f]*quantity[f] for f in foods) >= protein_req","sum(carbs[f]*quantity[f] for f in foods) >= carbs_req","sum(calories[f]*quantity[f] for f in foods) >= calories_req"],"objective":"minimize sum(cost[f]*quantity[f] for f in foods)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.foods = pyo.Set(
        initialize=["steak", "eggs", "pasta", "chicken"],
        ordered=True,
    )

    model.protein = pyo.Param(
        model.foods,
        initialize={
            "steak": params["protein_steak"],
            "eggs": params["protein_eggs"],
            "pasta": params["protein_pasta"],
            "chicken": params["protein_chicken"],
        },
    )
    model.carbs = pyo.Param(
        model.foods,
        initialize={
            "steak": params["carbs_steak"],
            "eggs": params["carbs_eggs"],
            "pasta": params["carbs_pasta"],
            "chicken": params["carbs_chicken"],
        },
    )
    model.calories = pyo.Param(
        model.foods,
        initialize={
            "steak": params["calories_steak"],
            "eggs": params["calories_eggs"],
            "pasta": params["calories_pasta"],
            "chicken": params["calories_chicken"],
        },
    )
    model.cost = pyo.Param(
        model.foods,
        initialize={
            "steak": params["cost_steak"],
            "eggs": params["cost_eggs"],
            "pasta": params["cost_pasta"],
            "chicken": params["cost_chicken"],
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
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}