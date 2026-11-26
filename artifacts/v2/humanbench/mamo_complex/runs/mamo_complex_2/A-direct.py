import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["bread", "milk", "fish", "potato"]

    protein = {
        f: params["protein_" + f] for f in foods
    }
    carbs = {
        f: params["carbs_" + f] for f in foods
    }
    calories = {
        f: params["calories_" + f] for f in foods
    }
    cost = {
        f: params["cost_" + f] for f in foods
    }

    model = pyo.ConcreteModel()

    model.FOODS = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.FOODS, within=pyo.NonNegativeReals)

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

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}