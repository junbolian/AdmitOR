import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    foods = ["Chicken", "Rice", "Apples", "Cheese", "Tofu"]
    idx = {f: i for i, f in enumerate(foods)}

    model = pyo.ConcreteModel()
    model.FOODS = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.FOODS, domain=pyo.NonNegativeIntegers)

    def protein_rule(m):
        return sum(params["protein_content"][idx[f]] * m.x[f] for f in m.FOODS) >= params["protein_requirement"]
    model.protein_con = pyo.Constraint(rule=protein_rule)

    def carb_rule(m):
        return sum(params["carb_content"][idx[f]] * m.x[f] for f in m.FOODS) >= params["carb_requirement"]
    model.carb_con = pyo.Constraint(rule=carb_rule)

    def calorie_rule(m):
        return sum(params["calorie_content"][idx[f]] * m.x[f] for f in m.FOODS) >= params["calorie_requirement"]
    model.calorie_con = pyo.Constraint(rule=calorie_rule)

    def obj_rule(m):
        return sum(params["cost"][idx[f]] * m.x[f] for f in m.FOODS)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}