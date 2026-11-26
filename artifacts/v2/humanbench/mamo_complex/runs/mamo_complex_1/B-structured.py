# IR: {"sets":{"foods":["steak","rice","chicken","lettuce","almonds"]},"params":["cost_steak","cost_rice","cost_chicken","cost_lettuce","cost_almonds","protein_steak","protein_rice","protein_chicken","protein_lettuce","protein_almonds","carbs_steak","carbs_rice","carbs_chicken","carbs_lettuce","carbs_almonds","calories_steak","calories_rice","calories_chicken","calories_lettuce","calories_almonds","protein_req","carbs_req","calories_req"],"variables":{"quantity[foods]":"NonNegativeReals"},"constraints":["sum(protein[f]*quantity[f] for f in foods) >= protein_req","sum(carbs[f]*quantity[f] for f in foods) >= carbs_req","sum(calories[f]*quantity[f] for f in foods) >= calories_req"],"objective":"minimize sum(cost[f]*quantity[f] for f in foods)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.foods = pyo.Set(
        initialize=["steak", "rice", "chicken", "lettuce", "almonds"],
        ordered=True,
    )

    model.cost = pyo.Param(
        model.foods,
        initialize={
            "steak": params["cost_steak"],
            "rice": params["cost_rice"],
            "chicken": params["cost_chicken"],
            "lettuce": params["cost_lettuce"],
            "almonds": params["cost_almonds"],
        },
    )
    model.protein = pyo.Param(
        model.foods,
        initialize={
            "steak": params["protein_steak"],
            "rice": params["protein_rice"],
            "chicken": params["protein_chicken"],
            "lettuce": params["protein_lettuce"],
            "almonds": params["protein_almonds"],
        },
    )
    model.carbs = pyo.Param(
        model.foods,
        initialize={
            "steak": params["carbs_steak"],
            "rice": params["carbs_rice"],
            "chicken": params["carbs_chicken"],
            "lettuce": params["carbs_lettuce"],
            "almonds": params["carbs_almonds"],
        },
    )
    model.calories = pyo.Param(
        model.foods,
        initialize={
            "steak": params["calories_steak"],
            "rice": params["calories_rice"],
            "chicken": params["calories_chicken"],
            "lettuce": params["calories_lettuce"],
            "almonds": params["calories_almonds"],
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
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}