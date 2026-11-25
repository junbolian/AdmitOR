import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = params["costs"]
    nutrient_min = params["nutrient_min"]
    nutrient_max = params["nutrient_max"]
    nutrient_coeffs = params["nutrient_coeffs"]

    num_foods = params["num_foods"]
    num_nutrients = params["num_nutrients"]

    food_idx = list(range(num_foods))
    nutr_idx = list(range(num_nutrients))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(food_idx, domain=pyo.NonNegativeReals)

    model.cost_expr = pyo.Expression(expr=sum(costs[i] * model.x[i] for i in food_idx))

    model.obj = pyo.Objective(expr=model.cost_expr, sense=pyo.minimize)

    def nutrient_min_rule(mdl, j):
        return sum(nutrient_coeffs[j][i] * mdl.x[i] for i in food_idx) >= nutrient_min[j]

    def nutrient_max_rule(mdl, j):
        return sum(nutrient_coeffs[j][i] * mdl.x[i] for i in food_idx) <= nutrient_max[j]

    model.nutrient_min_con = pyo.Constraint(nutr_idx, rule=nutrient_min_rule)
    model.nutrient_max_con = pyo.Constraint(nutr_idx, rule=nutrient_max_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}