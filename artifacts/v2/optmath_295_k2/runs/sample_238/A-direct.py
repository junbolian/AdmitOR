import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_foods = int(params["num_foods"])
    num_nutrients = int(params["num_nutrients"])

    food_cost = params["food_cost"]
    nutrient_min = params["nutrient_min"]
    nutrient_max = params["nutrient_max"]

    coeffs = []
    for j in range(num_nutrients):
        coeffs.append(params["nutrient_%d_coeff" % j])

    model = pyo.ConcreteModel()

    model.FOODS = pyo.RangeSet(0, num_foods - 1)
    model.NUTRIENTS = pyo.RangeSet(0, num_nutrients - 1)

    model.x = pyo.Var(model.FOODS, domain=pyo.NonNegativeReals)

    def cost_rule(mdl):
        return sum(food_cost[i] * mdl.x[i] for i in mdl.FOODS)

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def nutrient_min_rule(mdl, j):
        return sum(coeffs[j][i] * mdl.x[i] for i in mdl.FOODS) >= nutrient_min[j]

    def nutrient_max_rule(mdl, j):
        return sum(coeffs[j][i] * mdl.x[i] for i in mdl.FOODS) <= nutrient_max[j]

    model.min_constraints = pyo.Constraint(model.NUTRIENTS, rule=nutrient_min_rule)
    model.max_constraints = pyo.Constraint(model.NUTRIENTS, rule=nutrient_max_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}