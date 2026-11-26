import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["Chicken", "Rice", "Eggs", "Broccoli", "Lentils", "Apples"]

    cost_d = dict(zip(foods, params["cost"]))
    protein_d = dict(zip(foods, params["protein"]))
    carbs_d = dict(zip(foods, params["carbs"]))
    calories_d = dict(zip(foods, params["calories"]))
    protein_req = params["protein_req"]
    carb_req = params["carb_req"]
    calorie_req = params["calorie_req"]

    model = pyo.ConcreteModel()

    model.FOODS = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.FOODS, domain=pyo.NonNegativeReals)

    model.total_cost = pyo.Objective(
        expr=sum(cost_d[food] * model.x[food] for food in model.FOODS),
        sense=pyo.minimize,
    )

    model.protein_con = pyo.Constraint(
        expr=sum(protein_d[food] * model.x[food] for food in model.FOODS) >= protein_req
    )
    model.carb_con = pyo.Constraint(
        expr=sum(carbs_d[food] * model.x[food] for food in model.FOODS) >= carb_req
    )
    model.calorie_con = pyo.Constraint(
        expr=sum(calories_d[food] * model.x[food] for food in model.FOODS) >= calorie_req
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}