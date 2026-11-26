import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    foods = ["Steak", "Apples", "Eggs", "Chicken", "Tofu"]

    cost = params["cost_per_unit"]
    protein = params["protein_per_unit"]
    carbs = params["carbs_per_unit"]
    calories = params["calories_per_unit"]
    min_protein = params["min_protein"]
    min_carbs = params["min_carbs"]
    min_calories = params["min_calories"]

    cost_map = {f: cost[i] for i, f in enumerate(foods)}
    protein_map = {f: protein[i] for i, f in enumerate(foods)}
    carbs_map = {f: carbs[i] for i, f in enumerate(foods)}
    calories_map = {f: calories[i] for i, f in enumerate(foods)}

    model = pyo.ConcreteModel()

    model.FOODS = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.FOODS, domain=pyo.NonNegativeIntegers)

    def cost_rule(model):
        return sum(cost_map[food] * model.x[food] for food in model.FOODS)
    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def protein_rule(model):
        return sum(protein_map[food] * model.x[food] for food in model.FOODS) >= min_protein
    model.protein_constraint = pyo.Constraint(rule=protein_rule)

    def carbs_rule(model):
        return sum(carbs_map[food] * model.x[food] for food in model.FOODS) >= min_carbs
    model.carbs_constraint = pyo.Constraint(rule=carbs_rule)

    def calories_rule(model):
        return sum(calories_map[food] * model.x[food] for food in model.FOODS) >= min_calories
    model.calories_constraint = pyo.Constraint(rule=calories_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible or no solution"}