import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = [
        "chicken", "tofu", "brown_rice", "fish", "lentils",
        "quinoa", "eggs", "beef", "beans",
    ]

    costs = {
        "chicken": params["chicken_cost"],
        "tofu": params["tofu_cost"],
        "brown_rice": params["brown_rice_cost"],
        "fish": params["fish_cost"],
        "lentils": params["lentils_cost"],
        "quinoa": params["quinoa_cost"],
        "eggs": params["eggs_cost"],
        "beef": params["beef_cost"],
        "beans": params["beans_cost"],
    }

    protein = dict(zip(foods, params["protein_per_item"]))
    carbs = dict(zip(foods, params["carbs_per_item"]))
    calories = dict(zip(foods, params["calories_per_item"]))

    model = pyo.ConcreteModel()
    model.FOODS = pyo.Set(initialize=foods)

    model.portions = pyo.Var(model.FOODS, domain=pyo.NonNegativeIntegers)

    model.min_cost = pyo.Objective(
        expr=sum(costs[i] * model.portions[i] for i in model.FOODS),
        sense=pyo.minimize,
    )

    model.protein_req = pyo.Constraint(
        expr=sum(protein[i] * model.portions[i] for i in model.FOODS)
        >= params["protein_req"]
    )
    model.carbs_req = pyo.Constraint(
        expr=sum(carbs[i] * model.portions[i] for i in model.FOODS)
        >= params["carbs_req"]
    )
    model.calories_req = pyo.Constraint(
        expr=sum(calories[i] * model.portions[i] for i in model.FOODS)
        >= params["calories_req"]
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.min_cost))
    return {"objective": obj_val, "status": "optimal"}