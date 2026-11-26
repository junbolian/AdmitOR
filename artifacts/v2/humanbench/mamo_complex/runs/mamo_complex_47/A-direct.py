import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    costs = params["costs"]
    protein_coeffs = params["protein_coeffs"]
    carb_coeffs = params["carb_coeffs"]
    calorie_coeffs = params["calorie_coeffs"]
    protein_requirement = params["protein_requirement"]
    carb_requirement = params["carb_requirement"]
    calorie_requirement = params["calorie_requirement"]

    foods = list(range(len(costs)))

    model = pyo.ConcreteModel()
    model.x = pyo.Var(foods, within=pyo.NonNegativeReals)

    model.protein = pyo.Constraint(
        expr=sum(protein_coeffs[i] * model.x[i] for i in foods) >= protein_requirement
    )
    model.carbs = pyo.Constraint(
        expr=sum(carb_coeffs[i] * model.x[i] for i in foods) >= carb_requirement
    )
    model.calories = pyo.Constraint(
        expr=sum(calorie_coeffs[i] * model.x[i] for i in foods) >= calorie_requirement
    )
    model.cost = pyo.Objective(
        expr=sum(costs[i] * model.x[i] for i in foods), sense=pyo.minimize
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.cost))
    except Exception:
        return {"objective": None, "status": "infeasible or solve failed"}

    return {"objective": obj_val, "status": "optimal"}