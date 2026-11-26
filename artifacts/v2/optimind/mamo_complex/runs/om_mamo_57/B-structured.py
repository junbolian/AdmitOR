# {
#   "sets": {"foods": [0, 1, 2, 3, 4, 5]},
#   "params": {
#     "cost": "real[foods], from params['cost']",
#     "protein": "real[foods], from params['protein']",
#     "carbs": "real[foods], from params['carbs']",
#     "calories": "real[foods], from params['calories']",
#     "req_protein": "real, from params['req_protein']",
#     "req_carbs": "real, from params['req_carbs']",
#     "req_calories": "real, from params['req_calories']"
#   },
#   "variables": {"portions[i]": "nonnegative integer, i in foods"},
#   "constraints": [
#     "sum(protein[i] * portions[i] for i in foods) >= req_protein",
#     "sum(carbs[i] * portions[i] for i in foods) >= req_carbs",
#     "sum(calories[i] * portions[i] for i in foods) >= req_calories"
#   ],
#   "objective": "minimize sum(cost[i] * portions[i] for i in foods)"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Food parameter arrays use indices 0 through 5 for Food_1 through Food_6."""
    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=range(6), ordered=True)

    model.cost = pyo.Param(
        model.foods,
        initialize={i: params["cost"][i] for i in model.foods},
        within=pyo.Reals,
    )
    model.protein = pyo.Param(
        model.foods,
        initialize={i: params["protein"][i] for i in model.foods},
        within=pyo.Reals,
    )
    model.carbs = pyo.Param(
        model.foods,
        initialize={i: params["carbs"][i] for i in model.foods},
        within=pyo.Reals,
    )
    model.calories = pyo.Param(
        model.foods,
        initialize={i: params["calories"][i] for i in model.foods},
        within=pyo.Reals,
    )

    model.req_protein = pyo.Param(
        initialize=params["req_protein"], within=pyo.Reals
    )
    model.req_carbs = pyo.Param(
        initialize=params["req_carbs"], within=pyo.Reals
    )
    model.req_calories = pyo.Param(
        initialize=params["req_calories"], within=pyo.Reals
    )

    model.portions = pyo.Var(model.foods, domain=pyo.NonNegativeIntegers)

    model.protein_requirement = pyo.Constraint(
        expr=sum(
            model.protein[i] * model.portions[i] for i in model.foods
        ) >= model.req_protein
    )
    model.carbs_requirement = pyo.Constraint(
        expr=sum(
            model.carbs[i] * model.portions[i] for i in model.foods
        ) >= model.req_carbs
    )
    model.calories_requirement = pyo.Constraint(
        expr=sum(
            model.calories[i] * model.portions[i] for i in model.foods
        ) >= model.req_calories
    )

    model.total_cost = pyo.Objective(
        expr=sum(model.cost[i] * model.portions[i] for i in model.foods),
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