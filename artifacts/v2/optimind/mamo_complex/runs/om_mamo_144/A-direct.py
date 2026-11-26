import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    protein = params["protein_content"]
    carb = params["carb_content"]
    calorie = params["calorie_content"]
    cost = params["food_cost"]
    protein_req = params["protein_requirement"]
    carb_req = params["carb_requirement"]
    calorie_req = params["calorie_requirement"]

    foods = [0, 1, 2, 3]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(foods, domain=pyo.NonNegativeIntegers)

    model.cost_expr = pyo.Objective(
        expr=sum(cost[i] * model.x[i] for i in foods),
        sense=pyo.minimize,
    )

    model.protein_con = pyo.Constraint(
        expr=sum(protein[i] * model.x[i] for i in foods) >= protein_req
    )
    model.carb_con = pyo.Constraint(
        expr=sum(carb[i] * model.x[i] for i in foods) >= carb_req
    )
    model.calorie_con = pyo.Constraint(
        expr=sum(calorie[i] * model.x[i] for i in foods) >= calorie_req
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.cost_expr))
    return {"objective": obj_val, "status": "optimal"}