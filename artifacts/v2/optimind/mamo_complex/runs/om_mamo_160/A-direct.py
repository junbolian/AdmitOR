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

    foods = list(range(len(cost)))

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods)
    model.x = pyo.Var(model.foods, domain=pyo.NonNegativeIntegers)

    model.cost_expr = pyo.Expression(expr=sum(cost[i] * model.x[i] for i in model.foods))
    model.protein_con = pyo.Constraint(
        expr=sum(protein[i] * model.x[i] for i in model.foods) >= protein_req
    )
    model.carb_con = pyo.Constraint(
        expr=sum(carbs[i] * model.x[i] for i in model.foods) >= carb_req
    )
    model.calorie_con = pyo.Constraint(
        expr=sum(calories[i] * model.x[i] for i in model.foods) >= calorie_req
    )

    model.obj = pyo.Objective(expr=model.cost_expr, sense=pyo.minimize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible or failed"}