# IR: {"sets":{"foods":["Chicken","Pasta","Rice","Beans","Cheese"]},"params":{"protein":["protein_Chicken","protein_Pasta","protein_Rice","protein_Beans","protein_Cheese"],"carbs":["carbs_Chicken","carbs_Pasta","carbs_Rice","carbs_Beans","carbs_Cheese"],"calories":["calories_Chicken","calories_Pasta","calories_Rice","calories_Beans","calories_Cheese"],"cost":["cost_Chicken","cost_Pasta","cost_Rice","cost_Beans","cost_Cheese"],"protein_requirement":"protein_requirement","carbs_requirement":"carbs_requirement","calories_requirement":"calories_requirement"},"variables":{"portions[food]":"nonnegative integer"},"constraints":["sum(protein[food]*portions[food] for food in foods) >= protein_requirement","sum(carbs[food]*portions[food] for food in foods) >= carbs_requirement","sum(calories[food]*portions[food] for food in foods) >= calories_requirement"],"objective":"minimize sum(cost[food]*portions[food] for food in foods)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.foods = pyo.Set(
        initialize=["Chicken", "Pasta", "Rice", "Beans", "Cheese"],
        ordered=True,
    )

    model.protein = pyo.Param(
        model.foods,
        initialize={
            food: params[f"protein_{food}"] for food in model.foods
        },
    )
    model.carbs = pyo.Param(
        model.foods,
        initialize={
            food: params[f"carbs_{food}"] for food in model.foods
        },
    )
    model.calories = pyo.Param(
        model.foods,
        initialize={
            food: params[f"calories_{food}"] for food in model.foods
        },
    )
    model.cost = pyo.Param(
        model.foods,
        initialize={
            food: params[f"cost_{food}"] for food in model.foods
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