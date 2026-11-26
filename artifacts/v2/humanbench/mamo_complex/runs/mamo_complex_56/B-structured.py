# IR: {"sets":{"foods":["chicken","broccoli","beef","rice"]},"params":["cost_chicken","cost_broccoli","cost_beef","cost_rice","protein_chicken","protein_broccoli","protein_beef","protein_rice","carbs_chicken","carbs_broccoli","carbs_beef","carbs_rice","calories_chicken","calories_broccoli","calories_beef","calories_rice","protein_req","carbs_req","calories_req"],"variables":{"quantity[foods]":{"type":"continuous","lower_bound":0}},"constraints":["sum(protein[f]*quantity[f] for f in foods) >= protein_req","sum(carbs[f]*quantity[f] for f in foods) >= carbs_req","sum(calories[f]*quantity[f] for f in foods) >= calories_req"],"objective":{"sense":"minimize","expression":"sum(cost[f]*quantity[f] for f in foods)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.foods = pyo.Set(
        initialize=["chicken", "broccoli", "beef", "rice"],
        ordered=True,
    )

    model.unit_cost = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["cost_chicken"],
            "broccoli": params["cost_broccoli"],
            "beef": params["cost_beef"],
            "rice": params["cost_rice"],
        },
    )
    model.protein = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["protein_chicken"],
            "broccoli": params["protein_broccoli"],
            "beef": params["protein_beef"],
            "rice": params["protein_rice"],
        },
    )
    model.carbs = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["carbs_chicken"],
            "broccoli": params["carbs_broccoli"],
            "beef": params["carbs_beef"],
            "rice": params["carbs_rice"],
        },
    )
    model.calories = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["calories_chicken"],
            "broccoli": params["calories_broccoli"],
            "beef": params["calories_beef"],
            "rice": params["calories_rice"],
        },
    )

    model.protein_requirement = pyo.Param(initialize=params["protein_req"])
    model.carbs_requirement = pyo.Param(initialize=params["carbs_req"])
    model.calories_requirement = pyo.Param(initialize=params["calories_req"])

    model.quantity = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.quantity[food]
            for food in model.foods
        ) >= model.protein_requirement
    )
    model.carbs_minimum = pyo.Constraint(
        expr=sum(
            model.carbs[food] * model.quantity[food]
            for food in model.foods
        ) >= model.carbs_requirement
    )
    model.calories_minimum = pyo.Constraint(
        expr=sum(
            model.calories[food] * model.quantity[food]
            for food in model.foods
        ) >= model.calories_requirement
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[food] * model.quantity[food]
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