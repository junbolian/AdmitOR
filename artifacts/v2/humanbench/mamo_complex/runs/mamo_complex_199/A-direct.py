import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["bread", "milk", "fish", "potato"]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(foods, domain=pyo.NonNegativeReals)

    model.protein = pyo.Expression(
        expr=sum(params["protein_" + f] * model.x[f] for f in foods)
    )
    model.carb = pyo.Expression(
        expr=sum(params["carb_" + f] * model.x[f] for f in foods)
    )
    model.calorie = pyo.Expression(
        expr=sum(params["calorie_" + f] * model.x[f] for f in foods)
    )

    model.req_protein = pyo.Constraint(expr=model.protein >= params["req_protein"])
    model.req_carbs = pyo.Constraint(expr=model.carb >= params["req_carbs"])
    model.req_calories = pyo.Constraint(expr=model.calorie >= params["req_calories"])

    model.cost = pyo.Objective(
        expr=sum(params["cost_" + f] * model.x[f] for f in foods),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.cost))

    return {"objective": obj_val, "status": "optimal"}