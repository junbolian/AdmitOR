import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["Chicken", "Oats", "Tofu", "Rice", "Beef", "Salmon"]

    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    cost = params["cost"]

    protein_map = dict(zip(foods, protein))
    carbs_map = dict(zip(foods, carbs))
    calories_map = dict(zip(foods, calories))
    cost_map = dict(zip(foods, cost))

    model = pyo.ConcreteModel()
    model.F = pyo.Set(initialize=foods)
    model.x = pyo.Var(model.F, domain=pyo.NonNegativeReals)

    model.protein_rule = pyo.Constraint(
        expr=sum(protein_map[i] * model.x[i] for i in model.F) >= params["protein_target"]
    )
    model.carb_rule = pyo.Constraint(
        expr=sum(carbs_map[i] * model.x[i] for i in model.F) >= params["carb_target"]
    )
    model.calorie_rule = pyo.Constraint(
        expr=sum(calories_map[i] * model.x[i] for i in model.F) >= params["calorie_target"]
    )

    model.obj = pyo.Objective(
        expr=sum(cost_map[i] * model.x[i] for i in model.F), sense=pyo.minimize
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}