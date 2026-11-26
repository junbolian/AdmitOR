import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["chicken", "rice", "tofu", "spinach", "almonds", "salmon"]

    costs = params["costs"]
    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    req_protein = params["req_protein"]
    req_carbs = params["req_carbs"]
    req_calories = params["req_calories"]

    def get(d, f):
        if isinstance(d, dict):
            return d[f]
        return d[foods.index(f)]

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.F, domain=pyo.NonNegativeIntegers)

    def cost_rule(m):
        return sum(get(costs, f) * m.x[f] for f in m.F)

    model.cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def protein_rule(m):
        return sum(get(protein, f) * m.x[f] for f in m.F) >= req_protein

    def carbs_rule(m):
        return sum(get(carbs, f) * m.x[f] for f in m.F) >= req_carbs

    def calories_rule(m):
        return sum(get(calories, f) * m.x[f] for f in m.F) >= req_calories

    model.protein_con = pyo.Constraint(rule=protein_rule)
    model.carbs_con = pyo.Constraint(rule=carbs_rule)
    model.calories_con = pyo.Constraint(rule=calories_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}