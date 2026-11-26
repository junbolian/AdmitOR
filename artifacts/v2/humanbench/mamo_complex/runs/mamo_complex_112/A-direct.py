import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cost = params["cost"]
    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    req_protein_1 = params["req_protein_1"]
    req_protein_2 = params["req_protein_2"]
    req_calories = params["req_calories"]

    n = len(cost)
    foods = range(n)

    model = pyo.ConcreteModel()
    model.x = pyo.Var(foods, domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(cost[i] * model.x[i] for i in foods),
        sense=pyo.minimize,
    )

    model.protein_1 = pyo.Constraint(
        expr=sum(protein[i] * model.x[i] for i in foods) >= req_protein_1
    )
    model.protein_2 = pyo.Constraint(
        expr=sum(protein[i] * model.x[i] for i in foods) >= req_protein_2
    )
    model.calorie_req = pyo.Constraint(
        expr=sum(calories[i] * model.x[i] for i in foods) >= req_calories
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}