# IR: {"sets":{"foods":["Chicken","Rice","Broccoli","Eggs"]},"params":{"protein":{"Chicken":"protein_chicken","Rice":"protein_rice","Broccoli":"protein_broccoli","Eggs":"protein_eggs"},"carbs":{"Chicken":"carbs_chicken","Rice":"carbs_rice","Broccoli":"carbs_broccoli","Eggs":"carbs_eggs"},"calories":{"Chicken":"calories_chicken","Rice":"calories_rice","Broccoli":"calories_broccoli","Eggs":"calories_eggs"},"price":{"Chicken":"price_chicken","Rice":"price_rice","Broccoli":"price_broccoli","Eggs":"price_eggs"},"protein_requirement":"protein_requirement","carbs_requirement":"carbs_requirement","calories_requirement":"calories_requirement"},"variables":{"portions[food]":"NonNegativeIntegers"},"constraints":["sum(protein[food]*portions[food] for food in foods) >= protein_requirement","sum(carbs[food]*portions[food] for food in foods) >= carbs_requirement","sum(calories[food]*portions[food] for food in foods) >= calories_requirement"],"objective":{"sense":"minimize","expression":"sum(price[food]*portions[food] for food in foods)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.foods = pyo.Set(
        initialize=["Chicken", "Rice", "Broccoli", "Eggs"],
        ordered=True,
    )

    model.protein = pyo.Param(
        model.foods,
        initialize={
            "Chicken": params["protein_chicken"],
            "Rice": params["protein_rice"],
            "Broccoli": params["protein_broccoli"],
            "Eggs": params["protein_eggs"],
        },
    )
    model.carbs = pyo.Param(
        model.foods,
        initialize={
            "Chicken": params["carbs_chicken"],
            "Rice": params["carbs_rice"],
            "Broccoli": params["carbs_broccoli"],
            "Eggs": params["carbs_eggs"],
        },
    )
    model.calories = pyo.Param(
        model.foods,
        initialize={
            "Chicken": params["calories_chicken"],
            "Rice": params["calories_rice"],
            "Broccoli": params["calories_broccoli"],
            "Eggs": params["calories_eggs"],
        },
    )
    model.price = pyo.Param(
        model.foods,
        initialize={
            "Chicken": params["price_chicken"],
            "Rice": params["price_rice"],
            "Broccoli": params["price_broccoli"],
            "Eggs": params["price_eggs"],
        },
    )

    model.protein_requirement = pyo.Param(
        initialize=params["protein_requirement"]
    )
    model.carbs_requirement = pyo.Param(
        initialize=params["carbs_requirement"]
    )
    model.calories_requirement = pyo.Param(
        initialize=params["calories_requirement"]
    )

    model.portions = pyo.Var(
        model.foods,
        domain=pyo.NonNegativeIntegers,
    )

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.portions[food]
            for food in model.foods
        ) >= model.protein_requirement
    )
    model.carbs_minimum = pyo.Constraint(
        expr=sum(
            model.carbs[food] * model.portions[food]
            for food in model.foods
        ) >= model.carbs_requirement
    )
    model.calories_minimum = pyo.Constraint(
        expr=sum(
            model.calories[food] * model.portions[food]
            for food in model.foods
        ) >= model.calories_requirement
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.price[food] * model.portions[food]
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