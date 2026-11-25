import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_foods = int(params["num_foods"])
    num_nutrients = int(params["num_nutrients"])

    foods = list(range(num_foods))
    nutrients = list(range(num_nutrients))

    food_cost = params["food_cost"]
    nutrient_min = params["nutrient_min"]
    nutrient_max = params["nutrient_max"]

    coeff = {}
    for k in nutrients:
        coeff[k] = params["nutrient_" + str(k) + "_coeff"]

    model = pyo.ConcreteModel()

    model.FOOD = pyo.Set(initialize=foods)
    model.NUT = pyo.Set(initialize=nutrients)

    model.x = pyo.Var(model.FOOD, domain=pyo.NonNegativeReals)

    def cost_rule(m):
        return sum(food_cost[i] * m.x[i] for i in m.FOOD)

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def nutrient_lower_rule(m, k):
        return sum(coeff[k][i] * m.x[i] for i in m.FOOD) >= nutrient_min[k]

    def nutrient_upper_rule(m, k):
        return sum(coeff[k][i] * m.x[i] for i in m.FOOD) <= nutrient_max[k]

    model.nutrient_lower = pyo.Constraint(model.NUT, rule=nutrient_lower_rule)
    model.nutrient_upper = pyo.Constraint(model.NUT, rule=nutrient_upper_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}