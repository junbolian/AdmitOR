import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    protein_req = params["protein_req"]
    carbs_req = params["carbs_req"]
    calories_req = params["calories_req"]

    n = len(cost)
    items = list(range(n))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(items, domain=pyo.NonNegativeReals)

    model.total_cost = pyo.Objective(
        expr=sum(cost[i] * model.x[i] for i in items),
        sense=pyo.minimize,
    )

    model.protein_con = pyo.Constraint(
        expr=sum(protein[i] * model.x[i] for i in items) >= protein_req
    )
    model.carbs_con = pyo.Constraint(
        expr=sum(carbs[i] * model.x[i] for i in items) >= carbs_req
    )
    model.calories_con = pyo.Constraint(
        expr=sum(calories[i] * model.x[i] for i in items) >= calories_req
    )

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.total_cost))
    except Exception:
        return {"objective": None, "status": "infeasible"}

    return {"objective": obj_val, "status": "optimal"}