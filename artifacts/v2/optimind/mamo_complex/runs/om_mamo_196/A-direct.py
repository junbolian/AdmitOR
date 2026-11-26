import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    foods = ["Chicken", "Rice", "Apples", "Steak", "Lentils", "Fish", "Tofu", "Cheese", "Bread"]

    price = params["price"]
    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]

    # Build dict lookups in case params are provided as lists aligned with `foods`
    if isinstance(price, dict):
        price_d = {f: price[f] for f in foods}
    else:
        price_d = {f: price[i] for i, f in enumerate(foods)}

    if isinstance(protein, dict):
        protein_d = {f: protein[f] for f in foods}
    else:
        protein_d = {f: protein[i] for i, f in enumerate(foods)}

    if isinstance(carbs, dict):
        carbs_d = {f: carbs[f] for f in foods}
    else:
        carbs_d = {f: carbs[i] for i, f in enumerate(foods)}

    if isinstance(calories, dict):
        calories_d = {f: calories[f] for f in foods}
    else:
        calories_d = {f: calories[i] for i, f in enumerate(foods)}

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.F, domain=pyo.NonNegativeIntegers)

    model.cost = pyo.Objective(
        expr=sum(price_d[f] * model.x[f] for f in model.F),
        sense=pyo.minimize
    )

    model.protein_con = pyo.Constraint(
        expr=sum(protein_d[f] * model.x[f] for f in model.F) >= params["protein_req"]
    )
    model.carbs_con = pyo.Constraint(
        expr=sum(carbs_d[f] * model.x[f] for f in model.F) >= params["carbs_req"]
    )
    model.calories_con = pyo.Constraint(
        expr=sum(calories_d[f] * model.x[f] for f in model.F) >= params["calories_req"]
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}