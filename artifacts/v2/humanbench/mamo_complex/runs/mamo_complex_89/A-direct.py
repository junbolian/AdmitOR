import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    protein_req = params["protein_req"]
    carb_req = params["carb_req"]
    calorie_req = params["calorie_req"]

    n = len(cost)
    items = range(n)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(items, domain=pyo.NonNegativeReals)

    def cost_rule(m):
        return sum(cost[i] * m.x[i] for i in items)
    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def protein_rule(m):
        return sum(protein[i] * m.x[i] for i in items) >= protein_req
    model.protein_con = pyo.Constraint(rule=protein_rule)

    def carb_rule(m):
        return sum(carbs[i] * m.x[i] for i in items) >= carb_req
    model.carb_con = pyo.Constraint(rule=carb_rule)

    def calorie_rule(m):
        return sum(calories[i] * m.x[i] for i in items) >= calorie_req
    model.calorie_con = pyo.Constraint(rule=calorie_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}