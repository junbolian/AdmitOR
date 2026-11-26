import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["Eggs", "Chicken", "Tofu", "Salmon", "Brown Rice", "Spinach"]

    costs = params["costs"]
    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    protein_req = params["protein_req"]
    carb_req = params["carb_req"]
    calorie_req = params["calorie_req"]

    # Support both dict-style and positional list-style parameter data.
    def get_val(data, f, idx):
        if isinstance(data, dict):
            return data[f]
        return data[idx]

    cost_map = {f: get_val(costs, f, i) for i, f in enumerate(foods)}
    protein_map = {f: get_val(protein, f, i) for i, f in enumerate(foods)}
    carb_map = {f: get_val(carbs, f, i) for i, f in enumerate(foods)}
    calorie_map = {f: get_val(calories, f, i) for i, f in enumerate(foods)}

    model = pyo.ConcreteModel()

    model.FOODS = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.FOODS, domain=pyo.NonNegativeIntegers)

    def obj_rule(mod):
        return sum(cost_map[f] * mod.x[f] for f in mod.FOODS)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def protein_rule(mod):
        return sum(protein_map[f] * mod.x[f] for f in mod.FOODS) >= protein_req
    model.protein_con = pyo.Constraint(rule=protein_rule)

    def carb_rule(mod):
        return sum(carb_map[f] * mod.x[f] for f in mod.FOODS) >= carb_req
    model.carb_con = pyo.Constraint(rule=carb_rule)

    def calorie_rule(mod):
        return sum(calorie_map[f] * mod.x[f] for f in mod.FOODS) >= calorie_req
    model.calorie_con = pyo.Constraint(rule=calorie_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
    except Exception:
        return {"objective": None, "status": "infeasible or solver failure"}

    return {"objective": obj_val, "status": "optimal"}