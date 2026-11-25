import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    nutrient_min = params["nutrient_min"]
    nutrient_max = params["nutrient_max"]
    food_max_purchase = params["food_max_purchase"]
    nutrient_contribution = params["nutrient_contribution"]

    n_foods = 25
    n_nutrients = 7
    foods = list(range(n_foods))
    nutrients = list(range(n_nutrients))

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods)
    model.nutrients = pyo.Set(initialize=nutrients)

    model.Buy = pyo.Var(model.foods, within=pyo.NonNegativeReals,
                        bounds=(0, food_max_purchase))

    def obj_rule(m):
        return sum(cost[f] * m.Buy[f] for f in m.foods)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def nut_min_rule(m, n):
        return sum(nutrient_contribution[n][f] * m.Buy[f] for f in m.foods) >= nutrient_min[n]
    model.nut_min = pyo.Constraint(model.nutrients, rule=nut_min_rule)

    def nut_max_rule(m, n):
        return sum(nutrient_contribution[n][f] * m.Buy[f] for f in m.foods) <= nutrient_max[n]
    model.nut_max = pyo.Constraint(model.nutrients, rule=nut_max_rule)

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.total_cost))
    except Exception:
        return {"objective": None, "status": "infeasible or no solution found"}

    return {"objective": obj_val, "status": "optimal"}