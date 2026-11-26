import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["chicken", "rice", "broccoli", "eggs"]

    protein = {
        "chicken": params["protein_chicken"],
        "rice": params["protein_rice"],
        "broccoli": params["protein_broccoli"],
        "eggs": params["protein_eggs"],
    }
    carbs = {
        "chicken": params["carbs_chicken"],
        "rice": params["carbs_rice"],
        "broccoli": params["carbs_broccoli"],
        "eggs": params["carbs_eggs"],
    }
    calories = {
        "chicken": params["calories_chicken"],
        "rice": params["calories_rice"],
        "broccoli": params["calories_broccoli"],
        "eggs": params["calories_eggs"],
    }
    price = {
        "chicken": params["price_chicken"],
        "rice": params["price_rice"],
        "broccoli": params["price_broccoli"],
        "eggs": params["price_eggs"],
    }

    model = pyo.ConcreteModel()

    model.FOODS = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.FOODS, domain=pyo.NonNegativeIntegers)

    model.protein_req = pyo.Constraint(
        expr=sum(protein[f] * model.x[f] for f in foods)
        >= params["protein_requirement"]
    )
    model.carbs_req = pyo.Constraint(
        expr=sum(carbs[f] * model.x[f] for f in foods)
        >= params["carbs_requirement"]
    )
    model.calories_req = pyo.Constraint(
        expr=sum(calories[f] * model.x[f] for f in foods)
        >= params["calories_requirement"]
    )

    model.total_cost = pyo.Objective(
        expr=sum(price[f] * model.x[f] for f in foods), sense=pyo.minimize
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}