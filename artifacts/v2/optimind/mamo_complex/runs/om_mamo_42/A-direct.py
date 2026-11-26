import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    foods = ["Chicken", "Tuna", "Eggs", "Beef", "Rice", "Apples", "Bread"]

    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    price = params["price"]
    protein_target = params["protein_target"]
    carb_target = params["carb_target"]
    calorie_target = params["calorie_target"]

    model = pyo.ConcreteModel()
    model.FOODS = pyo.Set(initialize=foods)

    def protein_rule(model, f, i):
        return protein[i]

    model.protein_param = pyo.Param(model.FOODS, initialize={f: protein[i] for i, f in enumerate(foods)})
    model.carbs_param = pyo.Param(model.FOODS, initialize={f: carbs[i] for i, f in enumerate(foods)})
    model.calories_param = pyo.Param(model.FOODS, initialize={f: calories[i] for i, f in enumerate(foods)})
    model.price_param = pyo.Param(model.FOODS, initialize={f: price[i] for i, f in enumerate(foods)})

    model.x = pyo.Var(model.FOODS, domain=pyo.NonNegativeIntegers)

    model.protein_con = pyo.Constraint(
        expr=sum(model.protein_param[f] * model.x[f] for f in model.FOODS) >= protein_target
    )
    model.carb_con = pyo.Constraint(
        expr=sum(model.carbs_param[f] * model.x[f] for f in model.FOODS) >= carb_target
    )
    model.calorie_con = pyo.Constraint(
        expr=sum(model.calories_param[f] * model.x[f] for f in model.FOODS) >= calorie_target
    )

    model.cost = pyo.Objective(
        expr=sum(model.price_param[f] * model.x[f] for f in model.FOODS),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.cost))

    return {"objective": obj_val, "status": "optimal"}