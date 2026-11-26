# IR: {"sets":{"foods":["chicken","rice","broccoli","eggs"]},"params":["protein_chicken","protein_rice","protein_broccoli","protein_eggs","carbs_chicken","carbs_rice","carbs_broccoli","carbs_eggs","calories_chicken","calories_rice","calories_broccoli","calories_eggs","cost_chicken","cost_rice","cost_broccoli","cost_eggs","protein_requirement","carb_requirement","calorie_requirement"],"variables":{"quantity[food]":"NonNegativeReals"},"constraints":["sum(protein[food]*quantity[food] for food in foods) >= protein_requirement","sum(carbs[food]*quantity[food] for food in foods) >= carb_requirement","sum(calories[food]*quantity[food] for food in foods) >= calorie_requirement"],"objective":"minimize sum(cost[food]*quantity[food] for food in foods)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.foods = pyo.Set(
        initialize=["chicken", "rice", "broccoli", "eggs"],
        ordered=True,
    )

    model.protein = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["protein_chicken"],
            "rice": params["protein_rice"],
            "broccoli": params["protein_broccoli"],
            "eggs": params["protein_eggs"],
        },
    )
    model.carbs = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["carbs_chicken"],
            "rice": params["carbs_rice"],
            "broccoli": params["carbs_broccoli"],
            "eggs": params["carbs_eggs"],
        },
    )
    model.calories = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["calories_chicken"],
            "rice": params["calories_rice"],
            "broccoli": params["calories_broccoli"],
            "eggs": params["calories_eggs"],
        },
    )
    model.cost = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["cost_chicken"],
            "rice": params["cost_rice"],
            "broccoli": params["cost_broccoli"],
            "eggs": params["cost_eggs"],
        },
    )

    model.protein_requirement = pyo.Param(
        initialize=params["protein_requirement"]
    )
    model.carb_requirement = pyo.Param(
        initialize=params["carb_requirement"]
    )
    model.calorie_requirement = pyo.Param(
        initialize=params["calorie_requirement"]
    )

    model.quantity = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.quantity[food]
            for food in model.foods
        ) >= model.protein_requirement
    )
    model.carbohydrate_minimum = pyo.Constraint(
        expr=sum(
            model.carbs[food] * model.quantity[food]
            for food in model.foods
        ) >= model.carb_requirement
    )
    model.calorie_minimum = pyo.Constraint(
        expr=sum(
            model.calories[food] * model.quantity[food]
            for food in model.foods
        ) >= model.calorie_requirement
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