import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["steak", "eggs", "pasta", "chicken"]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(foods, domain=pyo.NonNegativeReals)

    model.protein = pyo.Constraint(
        expr=sum(params["protein_" + f] * model.x[f] for f in foods) >= params["protein_req"]
    )
    model.carbs = pyo.Constraint(
        expr=sum(params["carbs_" + f] * model.x[f] for f in foods) >= params["carbs_req"]
    )
    model.calories = pyo.Constraint(
        expr=sum(params["calories_" + f] * model.x[f] for f in foods) >= params["calories_req"]
    )

    model.cost = pyo.Objective(
        expr=sum(params["cost_" + f] * model.x[f] for f in foods),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}