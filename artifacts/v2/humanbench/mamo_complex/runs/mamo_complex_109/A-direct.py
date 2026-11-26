import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["Steak", "Apples", "Eggs", "Chicken", "Tofu"]

    cost_list = params["cost"]
    protein_list = params["protein"]
    carbs_list = params["carbs"]
    calories_list = params["calories"]
    protein_req = params["protein_req"]
    carb_req = params["carb_req"]
    calorie_req = params["calorie_req"]

    cost = {f: cost_list[i] for i, f in enumerate(foods)}
    protein = {f: protein_list[i] for i, f in enumerate(foods)}
    carbs = {f: carbs_list[i] for i, f in enumerate(foods)}
    calories = {f: calories_list[i] for i, f in enumerate(foods)}

    model = pyo.ConcreteModel()

    model.FOODS = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.FOODS, domain=pyo.NonNegativeReals)

    def cost_rule(m):
        return sum(cost[f] * m.x[f] for f in m.FOODS)

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def protein_rule(m):
        return sum(protein[f] * m.x[f] for f in m.FOODS) >= protein_req

    model.protein_con = pyo.Constraint(rule=protein_rule)

    def carb_rule(m):
        return sum(carbs[f] * m.x[f] for f in m.FOODS) >= carb_req

    model.carb_con = pyo.Constraint(rule=carb_rule)

    def calorie_rule(m):
        return sum(calories[f] * m.x[f] for f in m.FOODS) >= calorie_req

    model.calorie_con = pyo.Constraint(rule=calorie_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}