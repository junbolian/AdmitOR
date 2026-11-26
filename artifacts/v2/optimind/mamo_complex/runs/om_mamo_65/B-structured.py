# IR: {"sets":{"foods":["lentils","rice","chicken","beef","tofu"]},"params":["lentils_cost","rice_cost","chicken_cost","beef_cost","tofu_cost","lentils_protein","rice_protein","chicken_protein","beef_protein","tofu_protein","lentils_carbs","rice_carbs","chicken_carbs","beef_carbs","tofu_carbs","lentils_calories","rice_calories","chicken_calories","beef_calories","tofu_calories","protein_req","carbs_req","calories_req"],"variables":{"portions[foods]":"nonnegative integer"},"constraints":["sum(food_protein[f]*portions[f] for f in foods) >= protein_req","sum(food_carbs[f]*portions[f] for f in foods) >= carbs_req","sum(food_calories[f]*portions[f] for f in foods) >= calories_req"],"objective":"minimize sum(food_cost[f]*portions[f] for f in foods)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.foods = pyo.Set(
        initialize=["lentils", "rice", "chicken", "beef", "tofu"],
        ordered=True,
    )

    model.food_cost = pyo.Param(
        model.foods,
        within=pyo.Reals,
        initialize={
            "lentils": params["lentils_cost"],
            "rice": params["rice_cost"],
            "chicken": params["chicken_cost"],
            "beef": params["beef_cost"],
            "tofu": params["tofu_cost"],
        },
    )

    model.food_protein = pyo.Param(
        model.foods,
        within=pyo.Reals,
        initialize={
            "lentils": params["lentils_protein"],
            "rice": params["rice_protein"],
            "chicken": params["chicken_protein"],
            "beef": params["beef_protein"],
            "tofu": params["tofu_protein"],
        },
    )

    model.food_carbs = pyo.Param(
        model.foods,
        within=pyo.Reals,
        initialize={
            "lentils": params["lentils_carbs"],
            "rice": params["rice_carbs"],
            "chicken": params["chicken_carbs"],
            "beef": params["beef_carbs"],
            "tofu": params["tofu_carbs"],
        },
    )

    model.food_calories = pyo.Param(
        model.foods,
        within=pyo.Reals,
        initialize={
            "lentils": params["lentils_calories"],
            "rice": params["rice_calories"],
            "chicken": params["chicken_calories"],
            "beef": params["beef_calories"],
            "tofu": params["tofu_calories"],
        },
    )

    model.protein_requirement = pyo.Param(
        initialize=params["protein_req"], within=pyo.Reals
    )
    model.carbs_requirement = pyo.Param(
        initialize=params["carbs_req"], within=pyo.Reals
    )
    model.calories_requirement = pyo.Param(
        initialize=params["calories_req"], within=pyo.Reals
    )

    model.portions = pyo.Var(model.foods, domain=pyo.NonNegativeIntegers)

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.food_protein[food] * model.portions[food]
            for food in model.foods
        )
        >= model.protein_requirement
    )

    model.carbs_minimum = pyo.Constraint(
        expr=sum(
            model.food_carbs[food] * model.portions[food]
            for food in model.foods
        )
        >= model.carbs_requirement
    )

    model.calories_minimum = pyo.Constraint(
        expr=sum(
            model.food_calories[food] * model.portions[food]
            for food in model.foods
        )
        >= model.calories_requirement
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.food_cost[food] * model.portions[food]
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