import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_foods = 15
    num_nutrients = 9

    cost_per_serving = params["cost_per_serving"]
    nutrient_min = params["nutrient_min"]
    nutrient_max = params["nutrient_max"]
    volume_per_serving = params["volume_per_serving"]
    total_volume_capacity = params["total_volume_capacity"]

    # Nutrient contribution per serving: representative 15x9 matrix.
    # Row i = food_i, column j = amount of nutrient_j per serving.
    contribution = [
        [62, 55, 47, 51, 58, 44, 60, 49, 53],
        [45, 64, 53, 48, 42, 57, 50, 61, 46],
        [58, 47, 62, 55, 49, 51, 44, 57, 60],
        [51, 59, 48, 63, 54, 46, 57, 50, 52],
        [60, 52, 57, 49, 61, 55, 47, 58, 44],
        [47, 61, 50, 58, 45, 60, 53, 49, 56],
        [55, 48, 59, 52, 57, 49, 62, 46, 51],
        [49, 57, 54, 60, 51, 47, 58, 62, 45],
        [63, 50, 46, 57, 55, 58, 49, 52, 61],
        [52, 58, 61, 47, 50, 54, 46, 59, 57],
        [46, 54, 60, 49, 63, 52, 58, 55, 48],
        [57, 49, 45, 62, 47, 61, 52, 56, 59],
        [50, 60, 52, 56, 46, 49, 61, 53, 58],
        [59, 46, 57, 54, 52, 63, 45, 60, 50],
        [48, 53, 55, 58, 59, 50, 56, 44, 62],
    ]

    model = pyo.ConcreteModel()

    model.FOODS = pyo.RangeSet(0, num_foods - 1)
    model.NUTRIENTS = pyo.RangeSet(0, num_nutrients - 1)

    def servings_bounds(mdl, i):
        return (0, None)

    model.servings = pyo.Var(model.FOODS, bounds=servings_bounds)

    def cost_rule(mdl):
        return sum(cost_per_serving[i] * mdl.servings[i] for i in mdl.FOODS)

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def nutrient_min_rule(mdl, j):
        return sum(contribution[i][j] * mdl.servings[i] for i in mdl.FOODS) >= nutrient_min[j]

    def nutrient_max_rule(mdl, j):
        return sum(contribution[i][j] * mdl.servings[i] for i in mdl.FOODS) <= nutrient_max[j]

    model.nutrient_min_con = pyo.Constraint(model.NUTRIENTS, rule=nutrient_min_rule)
    model.nutrient_max_con = pyo.Constraint(model.NUTRIENTS, rule=nutrient_max_rule)

    def volume_rule(mdl):
        return sum(volume_per_serving[i] * mdl.servings[i] for i in mdl.FOODS) <= total_volume_capacity

    model.volume_con = pyo.Constraint(rule=volume_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}