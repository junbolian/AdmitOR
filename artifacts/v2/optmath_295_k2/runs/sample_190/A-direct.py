import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    nutrient_min = params["nutrient_min"]
    nutrient_max = params["nutrient_max"]
    food_max_purchase = params["food_max_purchase"]
    nutrient_contribution = params["nutrient_contribution"]

    n_foods = len(cost)
    n_nutrients = len(nutrient_min)

    # Normalize scalar food_max_purchase into per-food list if needed
    if isinstance(food_max_purchase, (int, float)):
        max_purchase = [food_max_purchase] * n_foods
    else:
        max_purchase = list(food_max_purchase)
        if len(max_purchase) == 1 and n_foods > 1:
            max_purchase = max_purchase * n_foods

    model = pyo.ConcreteModel()

    model.F = pyo.RangeSet(0, n_foods - 1)
    model.N = pyo.RangeSet(0, n_nutrients - 1)

    model.Buy = pyo.Var(model.F, bounds=lambda m, f: (0, max_purchase[f]))

    def obj_rule(m):
        return sum(cost[f] * m.Buy[f] for f in m.F)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def nutrient_min_rule(m, n):
        return sum(nutrient_contribution[n][f] * m.Buy[f] for f in m.F) >= nutrient_min[n]

    def nutrient_max_rule(m, n):
        return sum(nutrient_contribution[n][f] * m.Buy[f] for f in m.F) <= nutrient_max[n]

    model.nutrient_min_con = pyo.Constraint(model.N, rule=nutrient_min_rule)
    model.nutrient_max_con = pyo.Constraint(model.N, rule=nutrient_max_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}