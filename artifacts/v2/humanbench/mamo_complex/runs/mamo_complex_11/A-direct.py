import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    foods = ["Chicken", "Rice", "Beans", "Avocado"]
    costs_list = params["costs"]
    protein_list = params["protein_content"]
    carb_list = params["carb_content"]
    calorie_list = params["calorie_content"]
    protein_req = params["protein_req"]
    carb_req = params["carb_req"]
    calorie_req = params["calorie_req"]

    cost = {f: costs_list[k] for k, f in enumerate(foods)}
    protein = {f: protein_list[k] for k, f in enumerate(foods)}
    carbs = {f: carb_list[k] for k, f in enumerate(foods)}
    calories = {f: calorie_list[k] for k, f in enumerate(foods)}

    model = pyo.ConcreteModel()
    model.F = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.F, bounds=(0, None))

    model.cost = pyo.Objective(
        expr=sum(cost[i] * model.x[i] for i in model.F),
        sense=pyo.minimize,
    )

    model.protein_con = pyo.Constraint(
        expr=sum(protein[i] * model.x[i] for i in model.F) >= protein_req
    )
    model.carb_con = pyo.Constraint(
        expr=sum(carbs[i] * model.x[i] for i in model.F) >= carb_req
    )
    model.calorie_con = pyo.Constraint(
        expr=sum(calories[i] * model.x[i] for i in model.F) >= calorie_req
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}