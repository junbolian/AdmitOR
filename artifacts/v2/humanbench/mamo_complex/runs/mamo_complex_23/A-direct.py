import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["Beef", "Pasta", "Broccoli", "Chicken", "Apple",
             "Pork", "Lentils", "Eggs", "Cheese"]

    cost = params["cost"]
    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    req_protein = params["req_protein"]
    req_carbs = params["req_carbs"]
    req_calories = params["req_calories"]

    # Map food -> index, and helper to get value by food name from a
    # list (index) or dict (name) representation of params.
    def get(data, food):
        if isinstance(data, dict):
            return data[food]
        return data[foods.index(food)]

    model = pyo.ConcreteModel()
    model.FOODS = pyo.Set(initialize=foods)
    model.x = pyo.Var(model.FOODS, domain=pyo.NonNegativeReals)

    def cost_rule(m):
        return sum(get(cost, f) * m.x[f] for f in m.FOODS)
    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def protein_rule(m):
        return sum(get(protein, f) * m.x[f] for f in m.FOODS) >= req_protein
    model.protein_con = pyo.Constraint(rule=protein_rule)

    def carbs_rule(m):
        return sum(get(carbs, f) * m.x[f] for f in m.FOODS) >= req_carbs
    model.carbs_con = pyo.Constraint(rule=carbs_rule)

    def cal_rule(m):
        return sum(get(calories, f) * m.x[f] for f in m.FOODS) >= req_calories
    model.calories_con = pyo.Constraint(rule=cal_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}