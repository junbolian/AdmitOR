import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    foods = ["Pasta", "Avocado", "Chicken", "Tofu", "Spinach", "Cheese"]
    protein = dict(zip(foods, params["protein_grams"]))
    carbs = dict(zip(foods, params["carbs_grams"]))
    cals = dict(zip(foods, params["calories"]))
    cost = dict(zip(foods, params["cost"]))

    model = pyo.ConcreteModel()
    model.F = pyo.Set(initialize=foods)
    model.x = pyo.Var(model.F, domain=pyo.NonNegativeReals)

    model.cost_obj = pyo.Objective(
        expr=sum(cost[f] * model.x[f] for f in model.F),
        sense=pyo.minimize,
    )

    model.protein_con = pyo.Constraint(
        expr=sum(protein[f] * model.x[f] for f in model.F) >= params["protein_target"]
    )
    model.carb_con = pyo.Constraint(
        expr=sum(carbs[f] * model.x[f] for f in model.F) >= params["carb_target"]
    )
    model.cal_con = pyo.Constraint(
        expr=sum(cals[f] * model.x[f] for f in model.F) >= params["calorie_target"]
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.cost_obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible_or_failed"}