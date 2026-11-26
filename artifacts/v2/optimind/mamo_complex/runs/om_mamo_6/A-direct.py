import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    foods = list(range(9))
    costs = params["costs"]
    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    protein_target = params["protein_target"]
    carb_target = params["carb_target"]
    calorie_target = params["calorie_target"]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(foods, domain=pyo.NonNegativeIntegers)

    model.protein_con = pyo.Constraint(
        expr=sum(protein[i] * model.x[i] for i in foods) >= protein_target
    )
    model.carb_con = pyo.Constraint(
        expr=sum(carbs[i] * model.x[i] for i in foods) >= carb_target
    )
    model.calorie_con = pyo.Constraint(
        expr=sum(calories[i] * model.x[i] for i in foods) >= calorie_target
    )

    model.objective = pyo.Objective(
        expr=sum(costs[i] * model.x[i] for i in foods),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.objective))
    return {"objective": obj_val, "status": "optimal"}