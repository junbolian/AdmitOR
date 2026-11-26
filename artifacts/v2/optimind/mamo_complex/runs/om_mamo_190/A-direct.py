import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["chicken", "broccoli", "beef", "rice"]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(foods, domain=pyo.NonNegativeIntegers)

    model.cost = pyo.Objective(
        expr=sum(params["cost_" + f] * model.x[f] for f in foods),
        sense=pyo.minimize,
    )

    model.protein = pyo.Constraint(
        expr=sum(params["protein_" + f] * model.x[f] for f in foods)
        >= params["protein_target"]
    )
    model.carbs = pyo.Constraint(
        expr=sum(params["carbs_" + f] * model.x[f] for f in foods)
        >= params["carbs_target"]
    )
    model.calories = pyo.Constraint(
        expr=sum(params["calories_" + f] * model.x[f] for f in foods)
        >= params["calories_target"]
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}