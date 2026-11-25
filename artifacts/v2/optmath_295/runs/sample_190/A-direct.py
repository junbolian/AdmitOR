import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    food_cost = params["food_cost"]
    max_buy_per_food = params["max_buy_per_food"]
    nutrient_min = params["nutrient_min"]
    nutrient_max = params["nutrient_max"]
    nutrient_coefficients = params["nutrient_coefficients"]

    n_foods = len(food_cost)
    n_nutrients = len(nutrient_min)

    model = pyo.ConcreteModel()

    model.FOODS = pyo.RangeSet(0, n_foods - 1)
    model.NUTRIENTS = pyo.RangeSet(0, n_nutrients - 1)

    model.Buy = pyo.Var(model.FOODS, domain=pyo.NonNegativeReals,
                        bounds=(0, max_buy_per_food))

    def cost_rule(m):
        return sum(food_cost[i] * m.Buy[i] for i in m.FOODS)

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def nutrient_min_rule(m, j):
        return sum(nutrient_coefficients[j][i] * m.Buy[i] for i in m.FOODS) >= nutrient_min[j]

    def nutrient_max_rule(m, j):
        return sum(nutrient_coefficients[j][i] * m.Buy[i] for i in m.FOODS) <= nutrient_max[j]

    model.nutrient_min_con = pyo.Constraint(model.NUTRIENTS, rule=nutrient_min_rule)
    model.nutrient_max_con = pyo.Constraint(model.NUTRIENTS, rule=nutrient_max_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
    except Exception:
        return {"objective": None, "status": "infeasible"}

    if obj_val is None:
        return {"objective": None, "status": "infeasible"}

    return {"objective": obj_val, "status": "optimal"}