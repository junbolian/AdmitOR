import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["chicken", "broccoli", "beef", "rice"]

    model = pyo.ConcreteModel()
    model.FOODS = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.FOODS, domain=pyo.NonNegativeReals)

    cost = {
        "chicken": params["cost_chicken"],
        "broccoli": params["cost_broccoli"],
        "beef": params["cost_beef"],
        "rice": params["cost_rice"],
    }
    protein = {
        "chicken": params["protein_chicken"],
        "broccoli": params["protein_broccoli"],
        "beef": params["protein_beef"],
        "rice": params["protein_rice"],
    }
    carbs = {
        "chicken": params["carbs_chicken"],
        "broccoli": params["carbs_broccoli"],
        "beef": params["carbs_beef"],
        "rice": params["carbs_rice"],
    }
    calories = {
        "chicken": params["calories_chicken"],
        "broccoli": params["calories_broccoli"],
        "beef": params["calories_beef"],
        "rice": params["calories_rice"],
    }

    model.protein_con = pyo.Constraint(
        expr=sum(protein[f] * model.x[f] for f in model.FOODS)
        >= params["protein_req"]
    )
    model.carbs_con = pyo.Constraint(
        expr=sum(carbs[f] * model.x[f] for f in model.FOODS)
        >= params["carbs_req"]
    )
    model.calories_con = pyo.Constraint(
        expr=sum(calories[f] * model.x[f] for f in model.FOODS)
        >= params["calories_req"]
    )

    model.total_cost = pyo.Objective(
        expr=sum(cost[f] * model.x[f] for f in model.FOODS),
        sense=pyo.minimize,
    )

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}