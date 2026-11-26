import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ['brownies', 'chocolate_ice_cream', 'cola', 'pineapple_cheesecake']

    model = pyo.ConcreteModel()

    model.FOODS = pyo.Set(initialize=foods)

    calories = params["calories"]
    chocolate = params["chocolate"]
    sugar = params["sugar"]
    fat = params["fat"]
    cost = params["cost"]

    min_calories = params["min_calories"]
    min_chocolate = params["min_chocolate"]
    min_sugar = params["min_sugar"]
    min_fat = params["min_fat"]

    def calories_of(f):
        return calories[foods.index(f)] if isinstance(calories, (list, tuple)) else calories[f]

    def chocolate_of(f):
        return chocolate[foods.index(f)] if isinstance(chocolate, (list, tuple)) else chocolate[f]

    def sugar_of(f):
        return sugar[foods.index(f)] if isinstance(sugar, (list, tuple)) else sugar[f]

    def fat_of(f):
        return fat[foods.index(f)] if isinstance(fat, (list, tuple)) else fat[f]

    def cost_of(f):
        return cost[foods.index(f)] if isinstance(cost, (list, tuple)) else cost[f]

    model.x = pyo.Var(model.FOODS, domain=pyo.NonNegativeReals)

    def cost_rule(m):
        return sum(cost_of(f) * m.x[f] for f in m.FOODS)

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def cal_rule(m):
        return sum(calories_of(f) * m.x[f] for f in m.FOODS) >= min_calories

    model.cal_constraint = pyo.Constraint(rule=cal_rule)

    def choc_rule(m):
        return sum(chocolate_of(f) * m.x[f] for f in m.FOODS) >= min_chocolate

    model.choc_constraint = pyo.Constraint(rule=choc_rule)

    def sugar_rule(m):
        return sum(sugar_of(f) * m.x[f] for f in m.FOODS) >= min_sugar

    model.sugar_constraint = pyo.Constraint(rule=sugar_rule)

    def fat_rule(m):
        return sum(fat_of(f) * m.x[f] for f in m.FOODS) >= min_fat

    model.fat_constraint = pyo.Constraint(rule=fat_rule)

    try:
        Highs().solve(model)
    except Exception as exc:
        return {"objective": None, "status": "solver failed: " + str(exc)[:100]}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except Exception:
        return {"objective": None, "status": "infeasible or no solution"}

    return {"objective": obj_val, "status": "optimal"}