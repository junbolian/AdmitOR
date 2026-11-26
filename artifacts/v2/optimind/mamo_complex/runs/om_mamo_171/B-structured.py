# IR: {
#   "sets": {"foods": ["chicken", "cheese", "rice", "beans"]},
#   "params": {
#     "price": {"chicken": "price_chicken", "cheese": "price_cheese", "rice": "price_rice", "beans": "price_beans"},
#     "protein": {"chicken": "protein_chicken", "cheese": "protein_cheese", "rice": "protein_rice", "beans": "protein_beans"},
#     "carbs": {"chicken": "carbs_chicken", "cheese": "carbs_cheese", "rice": "carbs_rice", "beans": "carbs_beans"},
#     "calories": {"chicken": "calories_chicken", "cheese": "calories_cheese", "rice": "calories_rice", "beans": "calories_beans"},
#     "protein_req": "protein_req", "carbs_req": "carbs_req", "calories_req": "calories_req"
#   },
#   "decision_variables": {"quantity[food]": "continuous, nonnegative"},
#   "constraints": [
#     "sum(protein[food] * quantity[food] for food in foods) >= protein_req",
#     "sum(carbs[food] * quantity[food] for food in foods) >= carbs_req",
#     "sum(calories[food] * quantity[food] for food in foods) >= calories_req"
#   ],
#   "objective": "minimize sum(price[food] * quantity[food] for food in foods)"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.foods = pyo.Set(
        initialize=["chicken", "cheese", "rice", "beans"],
        ordered=True,
    )

    model.price = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["price_chicken"],
            "cheese": params["price_cheese"],
            "rice": params["price_rice"],
            "beans": params["price_beans"],
        },
        within=pyo.Reals,
    )
    model.protein = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["protein_chicken"],
            "cheese": params["protein_cheese"],
            "rice": params["protein_rice"],
            "beans": params["protein_beans"],
        },
        within=pyo.Reals,
    )
    model.carbs = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["carbs_chicken"],
            "cheese": params["carbs_cheese"],
            "rice": params["carbs_rice"],
            "beans": params["carbs_beans"],
        },
        within=pyo.Reals,
    )
    model.calories = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["calories_chicken"],
            "cheese": params["calories_cheese"],
            "rice": params["calories_rice"],
            "beans": params["calories_beans"],
        },
        within=pyo.Reals,
    )

    model.protein_req = pyo.Param(
        initialize=params["protein_req"], within=pyo.Reals
    )
    model.carbs_req = pyo.Param(
        initialize=params["carbs_req"], within=pyo.Reals
    )
    model.calories_req = pyo.Param(
        initialize=params["calories_req"], within=pyo.Reals
    )

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

    solver_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when no feasible solution can be loaded.
        solver_failed = True

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": "solve_failed" if solver_failed else "no_objective",
        }

    return {"objective": obj_val, "status": "optimal"}