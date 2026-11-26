import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["Food_1", "Food_2", "Food_3", "Food_4"]

    cost = {
        "Food_1": params["cost_food1"],
        "Food_2": params["cost_food2"],
        "Food_3": params["cost_food3"],
        "Food_4": params["cost_food4"],
    }
    protein = {
        "Food_1": params["protein_food1"],
        "Food_2": params["protein_food2"],
        "Food_3": params["protein_food3"],
        "Food_4": params["protein_food4"],
    }
    carb = {
        "Food_1": params["carb_food1"],
        "Food_2": params["carb_food2"],
        "Food_3": params["carb_food3"],
        "Food_4": params["carb_food4"],
    }
    calories = {
        "Food_1": params["calories_food1"],
        "Food_2": params["calories_food2"],
        "Food_3": params["calories_food3"],
        "Food_4": params["calories_food4"],
    }

    protein_req = params["protein_req"]
    carb_req = params["carb_req"]
    calorie_req = params["calorie_req"]

    model = pyo.ConcreteModel()

    model.FOODS = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.FOODS, domain=pyo.NonNegativeReals)

    def total_cost_rule(mdl):
        return sum(cost[f] * mdl.x[f] for f in mdl.FOODS)

    model.total_cost = pyo.Expression(rule=total_cost_rule)

    model.protein_con = pyo.Constraint(
        expr=sum(protein[f] * model.x[f] for f in model.FOODS) >= protein_req
    )
    model.carb_con = pyo.Constraint(
        expr=sum(carb[f] * model.x[f] for f in model.FOODS) >= carb_req
    )
    model.calorie_con = pyo.Constraint(
        expr=sum(calories[f] * model.x[f] for f in model.FOODS) >= calorie_req
    )

    model.obj = pyo.Objective(expr=model.total_cost, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}