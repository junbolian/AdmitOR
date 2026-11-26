import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    req_protein = params["req_protein"]
    req_carbs = params["req_carbs"]
    req_calories = params["req_calories"]

    foods = list(range(8))

    model = pyo.ConcreteModel()
    model.x = pyo.Var(foods, within=pyo.NonNegativeReals)

    model.protein_cons = pyo.Constraint(
        expr=sum(protein[i] * model.x[i] for i in foods) >= req_protein
    )
    model.carbs_cons = pyo.Constraint(
        expr=sum(carbs[i] * model.x[i] for i in foods) >= req_carbs
    )
    model.calories_cons = pyo.Constraint(
        expr=sum(calories[i] * model.x[i] for i in foods) >= req_calories
    )

    model.total_cost = pyo.Objective(
        expr=sum(cost[i] * model.x[i] for i in foods),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}