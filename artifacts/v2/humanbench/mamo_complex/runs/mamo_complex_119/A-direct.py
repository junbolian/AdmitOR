import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    foods = ["Chicken", "Rice", "Lentils", "Apples", "Eggs", "Broccoli"]

    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    cost = params["cost"]
    protein_req = params["protein_req"]
    carb_req = params["carb_req"]
    calorie_req = params["calorie_req"]

    protein_d = dict(zip(foods, protein))
    carbs_d = dict(zip(foods, carbs))
    calories_d = dict(zip(foods, calories))
    cost_d = dict(zip(foods, cost))

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_con = pyo.Constraint(
        expr=sum(protein_d[f] * model.x[f] for f in model.foods) >= protein_req
    )
    model.carb_con = pyo.Constraint(
        expr=sum(carbs_d[f] * model.x[f] for f in model.foods) >= carb_req
    )
    model.calorie_con = pyo.Constraint(
        expr=sum(calories_d[f] * model.x[f] for f in model.foods) >= calorie_req
    )

    model.total_cost = pyo.Objective(
        expr=sum(cost_d[f] * model.x[f] for f in model.foods),
        sense=pyo.minimize
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}