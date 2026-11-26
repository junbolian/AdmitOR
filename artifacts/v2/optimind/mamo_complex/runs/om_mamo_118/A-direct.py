import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    foods = ["Steak", "Tofu", "Chicken", "Broccoli", "Rice", "Spinach"]

    protein = params["protein_per_serving"]
    carbs = params["carb_per_serving"]
    calories = params["calories_per_serving"]
    cost = params["cost_per_serving"]

    protein_req = params["protein_requirement"]
    carb_req = params["carb_requirement"]
    calorie_req = params["calorie_requirement"]

    model = pyo.ConcreteModel()

    model.FOODS = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.FOODS, domain=pyo.NonNegativeIntegers)

    def protein_rule(m):
        return sum(protein[m.FOODS.ord(f) - 1] * m.x[f] for f in m.FOODS) >= protein_req
    model.protein_constraint = pyo.Constraint(rule=protein_rule)

    def carb_rule(m):
        return sum(carbs[m.FOODS.ord(f) - 1] * m.x[f] for f in m.FOODS) >= carb_req
    model.carb_constraint = pyo.Constraint(rule=carb_rule)

    def calorie_rule(m):
        return sum(calories[m.FOODS.ord(f) - 1] * m.x[f] for f in m.FOODS) >= calorie_req
    model.calorie_constraint = pyo.Constraint(rule=calorie_rule)

    def total_cost_rule(m):
        return sum(cost[m.FOODS.ord(f) - 1] * m.x[f] for f in m.FOODS)
    model.total_cost = pyo.Objective(rule=total_cost_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}