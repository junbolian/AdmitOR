import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["Food_1", "Food_2", "Food_3", "Food_4"]

    protein = params["protein_content"]
    carbs = params["carb_content"]
    calories = params["calorie_content"]
    cost = params["cost"]

    protein_req = params["protein_requirement"]
    carb_req = params["carb_requirement"]
    calorie_req = params["calorie_requirement"]

    def lookup(data, idx):
        # Support both dict-like and list-like inputs keyed by food name or position
        if isinstance(data, dict):
            return data[foods[idx]]
        return data[idx]

    model = pyo.ConcreteModel()

    model.FOODS = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.FOODS, domain=pyo.NonNegativeIntegers)

    model.protein_constraint = pyo.Constraint(
        expr=sum(lookup(protein, i) * model.x[foods[i]] for i in range(len(foods)))
        >= protein_req
    )
    model.carb_constraint = pyo.Constraint(
        expr=sum(lookup(carbs, i) * model.x[foods[i]] for i in range(len(foods)))
        >= carb_req
    )
    model.calorie_constraint = pyo.Constraint(
        expr=sum(lookup(calories, i) * model.x[foods[i]] for i in range(len(foods)))
        >= calorie_req
    )

    model.total_cost = pyo.Objective(
        expr=sum(lookup(cost, i) * model.x[foods[i]] for i in range(len(foods))),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}