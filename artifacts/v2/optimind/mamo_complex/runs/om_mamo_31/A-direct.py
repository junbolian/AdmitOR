import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["Chicken", "Tofu", "Rice", "Avocado"]

    cost = params["cost"]
    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    protein_req = params["protein_req"]
    carb_req = params["carb_req"]
    calorie_req = params["calorie_req"]

    def get_val(data, food):
        if isinstance(data, dict):
            return data[food]
        return data[foods.index(food)]

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=foods)
    model.x = pyo.Var(model.F, domain=pyo.NonNegativeIntegers)

    def total_cost_rule(mdl):
        return sum(get_val(cost, f) * mdl.x[f] for f in mdl.F)

    model.total_cost = pyo.Objective(rule=total_cost_rule, sense=pyo.minimize)

    def protein_rule(mdl):
        return sum(get_val(protein, f) * mdl.x[f] for f in mdl.F) >= protein_req

    def carb_rule(mdl):
        return sum(get_val(carbs, f) * mdl.x[f] for f in mdl.F) >= carb_req

    def calorie_rule(mdl):
        return sum(get_val(calories, f) * mdl.x[f] for f in mdl.F) >= calorie_req

    model.protein_con = pyo.Constraint(rule=protein_rule)
    model.carb_con = pyo.Constraint(rule=carb_rule)
    model.calorie_con = pyo.Constraint(rule=calorie_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))

    return {"objective": obj_val, "status": "optimal"}