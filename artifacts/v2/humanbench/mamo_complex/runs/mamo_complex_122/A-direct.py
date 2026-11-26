import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    foods = ["Chicken", "Tuna", "Eggs", "Beef", "Rice", "Apples", "Bread"]

    protein = params["protein_grams"]
    carbs = params["carb_grams"]
    cal = params["calories"]
    price = params["prices"]

    # Map food names to their position in the lists (lists may be passed by params)
    p_protein = {f: protein[i] for i, f in enumerate(foods)}
    p_carbs = {f: carbs[i] for i, f in enumerate(foods)}
    p_cal = {f: cal[i] for i, f in enumerate(foods)}
    p_price = {f: price[i] for i, f in enumerate(foods)}

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein = pyo.Constraint(
        expr=sum(p_protein[f] * model.x[f] for f in foods) >= params["protein_target"]
    )
    model.carbs = pyo.Constraint(
        expr=sum(p_carbs[f] * model.x[f] for f in foods) >= params["carb_target"]
    )
    model.calories = pyo.Constraint(
        expr=sum(p_cal[f] * model.x[f] for f in foods) >= params["calorie_target"]
    )

    model.cost = pyo.Objective(
        expr=sum(p_price[f] * model.x[f] for f in foods), sense=pyo.minimize
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}