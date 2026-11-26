import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["lentils", "rice", "chicken", "beef", "tofu"]

    cost = {f: params[f"{f}_cost"] for f in foods}
    protein = {f: params[f"{f}_protein"] for f in foods}
    carbs = {f: params[f"{f}_carbs"] for f in foods}
    calories = {f: params[f"{f}_calories"] for f in foods}

    model = pyo.ConcreteModel()
    model.FOODS = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.FOODS, domain=pyo.NonNegativeIntegers)

    model.cost_expr = pyo.Expression(
        expr=sum(cost[f] * model.x[f] for f in foods)
    )

    model.protein_con = pyo.Constraint(
        expr=sum(protein[f] * model.x[f] for f in foods) >= params["protein_req"]
    )
    model.carbs_con = pyo.Constraint(
        expr=sum(carbs[f] * model.x[f] for f in foods) >= params["carbs_req"]
    )
    model.calories_con = pyo.Constraint(
        expr=sum(calories[f] * model.x[f] for f in foods) >= params["calories_req"]
    )

    model.obj = pyo.Objective(expr=model.cost_expr, sense=pyo.minimize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible or failed"}

    return {"objective": obj_val, "status": "optimal"}