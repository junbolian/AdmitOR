import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["Eggs", "Grains", "Berries", "Nuts", "Salmon", "Vegetables", "Rice", "Meat"]

    costs = params["costs"]
    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    protein_req = params["protein_req"]
    carb_req = params["carb_req"]
    calorie_req = params["calorie_req"]

    model = pyo.ConcreteModel()
    model.FOODS = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.FOODS, within=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(costs[i] * model.x[food] for i, food in enumerate(model.FOODS)),
        sense=pyo.minimize,
    )

    model.protein_con = pyo.Constraint(
        expr=sum(protein[i] * model.x[food] for i, food in enumerate(model.FOODS)) >= protein_req
    )
    model.carb_con = pyo.Constraint(
        expr=sum(carbs[i] * model.x[food] for i, food in enumerate(model.FOODS)) >= carb_req
    )
    model.calorie_con = pyo.Constraint(
        expr=sum(calories[i] * model.x[food] for i, food in enumerate(model.FOODS)) >= calorie_req
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}