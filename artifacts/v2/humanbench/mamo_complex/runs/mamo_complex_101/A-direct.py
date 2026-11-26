import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["Steak", "Tofu", "Chicken", "Broccoli", "Rice", "Spinach"]

    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    cost = params["cost"]
    protein_req = params["protein_req"]
    carb_req = params["carb_req"]
    calorie_req = params["calorie_req"]

    # Build position lookup so we can handle either list or dict params
    def get_val(data, food, idx):
        if isinstance(data, dict):
            return data[food]
        return data[idx]

    protein_map = {food: get_val(protein, food, k) for k, food in enumerate(foods)}
    carbs_map = {food: get_val(carbs, food, k) for k, food in enumerate(foods)}
    calories_map = {food: get_val(calories, food, k) for k, food in enumerate(foods)}
    cost_map = {food: get_val(cost, food, k) for k, food in enumerate(foods)}

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_constraint = pyo.Constraint(
        expr=sum(protein_map[i] * model.x[i] for i in foods) >= protein_req
    )
    model.carb_constraint = pyo.Constraint(
        expr=sum(carbs_map[i] * model.x[i] for i in foods) >= carb_req
    )
    model.calorie_constraint = pyo.Constraint(
        expr=sum(calories_map[i] * model.x[i] for i in foods) >= calorie_req
    )

    model.total_cost = pyo.Objective(
        expr=sum(cost_map[i] * model.x[i] for i in foods),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))

    return {"objective": obj_val, "status": "optimal"}