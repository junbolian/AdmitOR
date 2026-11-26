import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    foods = ["steak", "eggs", "pasta", "chicken"]

    cost = {f: params["cost_" + f] for f in foods}
    protein = {f: params["protein_" + f] for f in foods}
    carbs = {f: params["carbs_" + f] for f in foods}
    calories = {f: params["calories_" + f] for f in foods}
    protein_req = params["protein_req"]
    carbs_req = params["carbs_req"]
    calories_req = params["calories_req"]

    model = pyo.ConcreteModel()
    model.FOODS = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.FOODS, domain=pyo.NonNegativeReals)

    model.protein_con = pyo.Constraint(
        expr=sum(protein[f] * model.x[f] for f in model.FOODS) >= protein_req
    )
    model.carbs_con = pyo.Constraint(
        expr=sum(carbs[f] * model.x[f] for f in model.FOODS) >= carbs_req
    )
    model.calories_con = pyo.Constraint(
        expr=sum(calories[f] * model.x[f] for f in model.FOODS) >= calories_req
    )

    model.obj = pyo.Objective(
        expr=sum(cost[f] * model.x[f] for f in model.FOODS),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception as exc:
        return {"objective": None, "status": "infeasible_or_failed"}