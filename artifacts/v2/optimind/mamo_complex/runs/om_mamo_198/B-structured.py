# IR: {
#   "sets": {"foods": ["pasta", "avocado", "chicken", "tofu", "spinach", "cheese"]},
#   "params": ["protein_pasta", "carb_pasta", "cal_pasta", "cost_pasta", "protein_avocado", "carb_avocado", "cal_avocado", "cost_avocado", "protein_chicken", "carb_chicken", "cal_chicken", "cost_chicken", "protein_tofu", "carb_tofu", "cal_tofu", "cost_tofu", "protein_spinach", "carb_spinach", "cal_spinach", "cost_spinach", "protein_cheese", "carb_cheese", "cal_cheese", "cost_cheese", "req_protein", "req_carb", "req_cal"],
#   "variables": {"portions[food]": "nonnegative integer"},
#   "constraints": [
#     "sum(protein[food] * portions[food] for food in foods) >= req_protein",
#     "sum(carb[food] * portions[food] for food in foods) >= req_carb",
#     "sum(cal[food] * portions[food] for food in foods) >= req_cal"
#   ],
#   "objective": "minimize sum(cost[food] * portions[food] for food in foods)"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.foods = pyo.Set(
        initialize=["pasta", "avocado", "chicken", "tofu", "spinach", "cheese"],
        ordered=True,
    )

    model.protein = pyo.Param(
        model.foods,
        initialize={
            "pasta": params["protein_pasta"],
            "avocado": params["protein_avocado"],
            "chicken": params["protein_chicken"],
            "tofu": params["protein_tofu"],
            "spinach": params["protein_spinach"],
            "cheese": params["protein_cheese"],
        },
    )
    model.carb = pyo.Param(
        model.foods,
        initialize={
            "pasta": params["carb_pasta"],
            "avocado": params["carb_avocado"],
            "chicken": params["carb_chicken"],
            "tofu": params["carb_tofu"],
            "spinach": params["carb_spinach"],
            "cheese": params["carb_cheese"],
        },
    )
    model.cal = pyo.Param(
        model.foods,
        initialize={
            "pasta": params["cal_pasta"],
            "avocado": params["cal_avocado"],
            "chicken": params["cal_chicken"],
            "tofu": params["cal_tofu"],
            "spinach": params["cal_spinach"],
            "cheese": params["cal_cheese"],
        },
    )
    model.cost = pyo.Param(
        model.foods,
        initialize={
            "pasta": params["cost_pasta"],
            "avocado": params["cost_avocado"],
            "chicken": params["cost_chicken"],
            "tofu": params["cost_tofu"],
            "spinach": params["cost_spinach"],
            "cheese": params["cost_cheese"],
        },
    )
    model.req_protein = pyo.Param(initialize=params["req_protein"])
    model.req_carb = pyo.Param(initialize=params["req_carb"])
    model.req_cal = pyo.Param(initialize=params["req_cal"])

    model.portions = pyo.Var(model.foods, domain=pyo.NonNegativeIntegers)

    model.protein_requirement = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.portions[food] for food in model.foods
        ) >= model.req_protein
    )
    model.carb_requirement = pyo.Constraint(
        expr=sum(
            model.carb[food] * model.portions[food] for food in model.foods
        ) >= model.req_carb
    )
    model.calorie_requirement = pyo.Constraint(
        expr=sum(
            model.cal[food] * model.portions[food] for food in model.foods
        ) >= model.req_cal
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[food] * model.portions[food] for food in model.foods
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