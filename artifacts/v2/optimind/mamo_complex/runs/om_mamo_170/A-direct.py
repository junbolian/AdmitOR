import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["Food_1", "Food_2", "Food_3", "Food_4", "Food_5"]

    protein = {foods[i]: params["protein_content"][i] for i in range(5)}
    carbs = {foods[i]: params["carb_content"][i] for i in range(5)}
    calories = {foods[i]: params["calorie_content"][i] for i in range(5)}
    cost = {foods[i]: params["food_cost"][i] for i in range(5)}

    model = pyo.ConcreteModel()
    model.FOODS = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.FOODS, domain=pyo.NonNegativeIntegers)

    model.protein_rule = pyo.Constraint(
        expr=sum(protein[f] * model.x[f] for f in model.FOODS) >= params["protein_target"]
    )
    model.carb_rule = pyo.Constraint(
        expr=sum(carbs[f] * model.x[f] for f in model.FOODS) >= params["carb_target"]
    )
    model.calorie_rule = pyo.Constraint(
        expr=sum(calories[f] * model.x[f] for f in model.FOODS) >= params["calorie_target"]
    )

    model.total_cost = pyo.Objective(
        expr=sum(cost[f] * model.x[f] for f in model.FOODS),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except Exception:
        return {"objective": None, "status": "solver failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except Exception:
        return {"objective": None, "status": "no feasible solution"}

    return {"objective": obj_val, "status": "optimal"}