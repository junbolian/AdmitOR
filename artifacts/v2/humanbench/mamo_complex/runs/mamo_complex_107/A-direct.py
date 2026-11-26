import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    protein_req = params["protein_req"]
    carbs_req = params["carbs_req"]
    calorie_req = params["calorie_req"]

    foods = list(range(len(cost)))

    model = pyo.ConcreteModel()
    model.x = pyo.Var(foods, domain=pyo.NonNegativeReals)

    model.protein_con = pyo.Constraint(
        expr=sum(protein[i] * model.x[i] for i in foods) >= protein_req
    )
    model.carbs_con = pyo.Constraint(
        expr=sum(carbs[i] * model.x[i] for i in foods) >= carbs_req
    )
    model.calorie_con = pyo.Constraint(
        expr=sum(calories[i] * model.x[i] for i in foods) >= calorie_req
    )

    model.total_cost = pyo.Objective(
        expr=sum(cost[i] * model.x[i] for i in foods),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}