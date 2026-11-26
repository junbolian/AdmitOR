# IR: {"sets":{"foods":["chicken","broccoli","beef","rice"]},"params":["cost_chicken","cost_broccoli","cost_beef","cost_rice","protein_chicken","protein_broccoli","protein_beef","protein_rice","carbs_chicken","carbs_broccoli","carbs_beef","carbs_rice","calories_chicken","calories_broccoli","calories_beef","calories_rice","protein_target","carbs_target","calories_target"],"variables":{"portions[food]":{"type":"nonnegative_integer"}},"constraints":["sum(protein[food]*portions[food] for food in foods) >= protein_target","sum(carbs[food]*portions[food] for food in foods) >= carbs_target","sum(calories[food]*portions[food] for food in foods) >= calories_target"],"objective":{"sense":"minimize","expression":"sum(cost[food]*portions[food] for food in foods)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.foods = pyo.Set(
        initialize=["chicken", "broccoli", "beef", "rice"],
        ordered=True,
    )

    model.cost = pyo.Param(
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

    model.protein_target = pyo.Param(initialize=params["protein_target"])
    model.carbs_target = pyo.Param(initialize=params["carbs_target"])
    model.calories_target = pyo.Param(initialize=params["calories_target"])

    model.portions = pyo.Var(model.foods, domain=pyo.NonNegativeIntegers)

    model.protein_requirement = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.portions[food]
            for food in model.foods
        ) >= model.protein_target
    )
    model.carbs_requirement = pyo.Constraint(
        expr=sum(
            model.carbs[food] * model.portions[food]
            for food in model.foods
        ) >= model.carbs_target
    )
    model.calories_requirement = pyo.Constraint(
        expr=sum(
            model.calories[food] * model.portions[food]
            for food in model.foods
        ) >= model.calories_target
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
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}