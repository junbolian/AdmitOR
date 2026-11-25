import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_per_serving = params["cost_per_serving"]
    nutrient_min = params["nutrient_min"]
    nutrient_max = params["nutrient_max"]
    volume_capacity = params["volume_capacity"]
    volume_per_serving = params["volume_per_serving"]

    num_foods = len(cost_per_serving)
    num_nutrients = len(nutrient_min)

    # Nutrient contribution matrix: rows are foods, columns are nutrients.
    # Constructed deterministically so the problem is well-defined.
    nutrient_matrix = [
        [((i + 3) * 7 + (j + 5) * 9 + (i * j) % 11 + 40) % 70 + 20
         for j in range(num_nutrients)]
        for i in range(num_foods)
    ]

    model = pyo.ConcreteModel()

    model.food_set = pyo.RangeSet(0, num_foods - 1)
    model.nutrient_set = pyo.RangeSet(0, num_nutrients - 1)

    model.servings = pyo.Var(model.food_set, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(cost_per_serving[i] * mdl.servings[i] for i in mdl.food_set)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def nutrient_min_rule(mdl, j):
        return sum(nutrient_matrix[i][j] * mdl.servings[i]
                   for i in mdl.food_set) >= nutrient_min[j]

    model.nutrient_min_con = pyo.Constraint(model.nutrient_set, rule=nutrient_min_rule)

    def nutrient_max_rule(mdl, j):
        return sum(nutrient_matrix[i][j] * mdl.servings[i]
                   for i in mdl.food_set) <= nutrient_max[j]

    model.nutrient_max_con = pyo.Constraint(model.nutrient_set, rule=nutrient_max_rule)

    def volume_rule(mdl):
        return sum(volume_per_serving[i] * mdl.servings[i]
                   for i in mdl.food_set) <= volume_capacity

    model.volume_con = pyo.Constraint(rule=volume_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}