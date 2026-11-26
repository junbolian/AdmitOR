import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["bread", "milk", "fish", "potato"]

    protein = params["protein_content"]
    carbs = params["carb_content"]
    calories = params["calorie_content"]
    cost = params["cost_per_unit"]

    protein_req = params["protein_requirement"]
    carb_req = params["carb_requirement"]
    calorie_req = params["calorie_requirement"]

    model = pyo.ConcreteModel()
    model.F = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.F, domain=pyo.NonNegativeReals)

    model.protein_con = pyo.Constraint(
        expr=sum(protein[i] * model.x[f] for i, f in enumerate(foods)) >= protein_req
    )
    model.carb_con = pyo.Constraint(
        expr=sum(carbs[i] * model.x[f] for i, f in enumerate(foods)) >= carb_req
    )
    model.calorie_con = pyo.Constraint(
        expr=sum(calories[i] * model.x[f] for i, f in enumerate(foods)) >= calorie_req
    )

    model.obj = pyo.Objective(
        expr=sum(cost[i] * model.x[f] for i, f in enumerate(foods)),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}