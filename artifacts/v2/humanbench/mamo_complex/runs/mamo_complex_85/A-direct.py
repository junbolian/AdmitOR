import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    protein_req = params["protein_req"]
    carb_req = params["carb_req"]
    calorie_req = params["calorie_req"]

    n = len(cost)
    foods = list(range(n))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(foods, domain=pyo.NonNegativeReals)

    model.protein_constraint = pyo.Constraint(
        expr=sum(protein[i] * model.x[i] for i in foods) >= protein_req
    )
    model.carb_constraint = pyo.Constraint(
        expr=sum(carbs[i] * model.x[i] for i in foods) >= carb_req
    )
    model.calorie_constraint = pyo.Constraint(
        expr=sum(calories[i] * model.x[i] for i in foods) >= calorie_req
    )

    model.objective_fn = pyo.Objective(
        expr=sum(cost[i] * model.x[i] for i in foods),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.objective_fn))
    return {"objective": obj_val, "status": "optimal"}