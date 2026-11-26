import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    foods = ["chicken", "rice", "beans", "avocado"]

    model = pyo.ConcreteModel()
    model.x = pyo.Var(foods, domain=pyo.NonNegativeIntegers)

    protein = {f: params[f"protein_{f}"] for f in foods}
    carb = {f: params[f"carb_{f}"] for f in foods}
    cal = {f: params[f"cal_{f}"] for f in foods}
    cost = {f: params[f"cost_{f}"] for f in foods}

    model.protein_con = pyo.Constraint(
        expr=sum(protein[f] * model.x[f] for f in foods) >= params["protein_goal"]
    )
    model.carb_con = pyo.Constraint(
        expr=sum(carb[f] * model.x[f] for f in foods) >= params["carb_goal"]
    )
    model.calorie_con = pyo.Constraint(
        expr=sum(cal[f] * model.x[f] for f in foods) >= params["calorie_goal"]
    )

    model.obj_expr = pyo.Objective(
        expr=sum(cost[f] * model.x[f] for f in foods), sense=pyo.minimize
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj_expr))
    return {"objective": obj_val, "status": "optimal"}