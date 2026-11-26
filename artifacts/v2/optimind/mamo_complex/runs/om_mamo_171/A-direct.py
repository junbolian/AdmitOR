import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    foods = ['chicken', 'cheese', 'rice', 'beans']

    model = pyo.ConcreteModel()

    model.x = pyo.Var(foods, domain=pyo.NonNegativeReals)

    def cost_rule(m):
        return sum(params["price_" + f] * m.x[f] for f in foods)
    model.cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def protein_rule(m):
        return sum(params["protein_" + f] * m.x[f] for f in foods) >= params["protein_req"]
    model.protein_con = pyo.Constraint(rule=protein_rule)

    def carbs_rule(m):
        return sum(params["carbs_" + f] * m.x[f] for f in foods) >= params["carbs_req"]
    model.carbs_con = pyo.Constraint(rule=carbs_rule)

    def calories_rule(m):
        return sum(params["calories_" + f] * m.x[f] for f in foods) >= params["calories_req"]
    model.calories_con = pyo.Constraint(rule=calories_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}