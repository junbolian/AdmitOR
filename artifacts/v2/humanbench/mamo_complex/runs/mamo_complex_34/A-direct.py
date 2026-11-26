import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    foods = ["chicken", "tofu", "rice", "avocado"]
    nutrients = ["protein", "carbs", "calories"]

    model = pyo.ConcreteModel()

    # Decision variables: servings of each food (continuous, nonnegative)
    model.x = pyo.Var(foods, domain=pyo.NonNegativeReals)

    # Objective: minimize total cost
    def cost_rule(m):
        return sum(params["cost_" + f] * m.x[f] for f in foods)
    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    # Nutritional constraints
    def protein_rule(m):
        return sum(params["protein_" + f] * m.x[f] for f in foods) >= params["protein_min"]
    model.protein_constraint = pyo.Constraint(rule=protein_rule)

    def carbs_rule(m):
        return sum(params["carbs_" + f] * m.x[f] for f in foods) >= params["carbs_min"]
    model.carbs_constraint = pyo.Constraint(rule=carbs_rule)

    def calories_rule(m):
        return sum(params["calories_" + f] * m.x[f] for f in foods) >= params["calories_min"]
    model.calories_constraint = pyo.Constraint(rule=calories_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}