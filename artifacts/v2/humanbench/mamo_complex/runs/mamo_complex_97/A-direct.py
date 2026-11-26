import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = [
        "chicken_breast",
        "tofu",
        "spinach",
        "beef_steak",
        "eggs",
        "brown_rice",
        "bananas",
        "quinoa",
    ]
    food_index = {food_name: i for i, food_name in enumerate(foods)}

    cost = params["cost"]
    protein_content = params["protein_content"]
    carb_content = params["carb_content"]
    calorie_content = params["calorie_content"]

    protein_requirement = params["protein_requirement"]
    carb_requirement = params["carb_requirement"]
    calorie_requirement = params["calorie_requirement"]

    model = pyo.ConcreteModel()

    model.FOODS = pyo.Set(initialize=foods)
    model.x = pyo.Var(model.FOODS, domain=pyo.NonNegativeReals)

    def cost_rule(m):
        return sum(cost[food_index[f]] * m.x[f] for f in m.FOODS)

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def protein_rule(m):
        return sum(protein_content[food_index[f]] * m.x[f] for f in m.FOODS) >= protein_requirement

    model.protein_constraint = pyo.Constraint(rule=protein_rule)

    def carb_rule(m):
        return sum(carb_content[food_index[f]] * m.x[f] for f in m.FOODS) >= carb_requirement

    model.carb_constraint = pyo.Constraint(rule=carb_rule)

    def calorie_rule(m):
        return sum(calorie_content[food_index[f]] * m.x[f] for f in m.FOODS) >= calorie_requirement

    model.calorie_constraint = pyo.Constraint(rule=calorie_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}