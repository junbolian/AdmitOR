import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    cost = params["cost"]
    protein_req = params["protein_req"]
    carb_req = params["carb_req"]
    cal_req = params["cal_req"]

    foods = list(range(5))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(foods, within=pyo.NonNegativeIntegers)

    model.protein_con = pyo.Constraint(
        expr=sum(protein[i] * model.x[i] for i in foods) >= protein_req
    )
    model.carb_con = pyo.Constraint(
        expr=sum(carbs[i] * model.x[i] for i in foods) >= carb_req
    )
    model.cal_con = pyo.Constraint(
        expr=sum(calories[i] * model.x[i] for i in foods) >= cal_req
    )

    model.total_cost = pyo.Objective(
        expr=sum(cost[i] * model.x[i] for i in foods), sense=pyo.minimize
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible or failed"}