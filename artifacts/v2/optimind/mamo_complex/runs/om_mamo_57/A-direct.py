import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    req_protein = params["req_protein"]
    req_carbs = params["req_carbs"]
    req_calories = params["req_calories"]

    foods = list(range(len(cost)))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(foods, domain=pyo.NonNegativeIntegers)

    model.protein_con = pyo.Constraint(
        expr=sum(protein[i] * model.x[i] for i in foods) >= req_protein
    )
    model.carbs_con = pyo.Constraint(
        expr=sum(carbs[i] * model.x[i] for i in foods) >= req_carbs
    )
    model.calories_con = pyo.Constraint(
        expr=sum(calories[i] * model.x[i] for i in foods) >= req_calories
    )

    model.total_cost = pyo.Objective(
        expr=sum(cost[i] * model.x[i] for i in foods),
        sense=pyo.minimize,
    )

    solver = Highs()
    solver.solve(model)

    try:
        obj_val = float(pyo.value(model.total_cost))
    except Exception:
        return {"objective": None, "status": "infeasible"}

    if obj_val is None:
        return {"objective": None, "status": "infeasible"}

    return {"objective": obj_val, "status": "optimal"}