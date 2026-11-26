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

    model = pyo.ConcreteModel()
    model.x = pyo.Var(range(n), within=pyo.NonNegativeIntegers)

    model.protein_con = pyo.Constraint(
        expr=sum(protein[i] * model.x[i] for i in range(n)) >= protein_req
    )
    model.carb_con = pyo.Constraint(
        expr=sum(carbs[i] * model.x[i] for i in range(n)) >= carb_req
    )
    model.calorie_con = pyo.Constraint(
        expr=sum(calories[i] * model.x[i] for i in range(n)) >= calorie_req
    )

    model.obj = pyo.Objective(
        expr=sum(cost[i] * model.x[i] for i in range(n)),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible"}

    return {"objective": obj_val, "status": "optimal"}