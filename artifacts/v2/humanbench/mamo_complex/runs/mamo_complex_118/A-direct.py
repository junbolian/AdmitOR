import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    foods = ["Chicken", "Pasta", "Apples", "Tuna", "Rice"]

    protein_data = params["protein"]
    carbs_data = params["carbs"]
    calories_data = params["calories"]
    price_data = params["price"]

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_req = pyo.Constraint(
        expr=sum(protein_data[i] * model.x[f] for i, f in enumerate(foods)) >= params["protein_requirement"]
    )
    model.carb_req = pyo.Constraint(
        expr=sum(carbs_data[i] * model.x[f] for i, f in enumerate(foods)) >= params["carb_requirement"]
    )
    model.calorie_req = pyo.Constraint(
        expr=sum(calories_data[i] * model.x[f] for i, f in enumerate(foods)) >= params["calorie_requirement"]
    )

    model.cost = pyo.Objective(
        expr=sum(price_data[i] * model.x[f] for i, f in enumerate(foods)),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}