import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    foods = ["Chicken", "Rice", "Vegetables", "Bread", "Almonds", "Salmon"]

    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    cost = params["cost"]

    def get_val(container, food):
        if isinstance(container, dict):
            return container[food]
        return container[foods.index(food)]

    model = pyo.ConcreteModel()
    model.F = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.F, domain=pyo.NonNegativeReals)

    model.protein_con = pyo.Constraint(
        expr=sum(get_val(protein, f) * model.x[f] for f in model.F) >= params["protein_requirement"]
    )
    model.carb_con = pyo.Constraint(
        expr=sum(get_val(carbs, f) * model.x[f] for f in model.F) >= params["carb_requirement"]
    )
    model.calorie_con = pyo.Constraint(
        expr=sum(get_val(calories, f) * model.x[f] for f in model.F) >= params["calorie_requirement"]
    )

    model.total_cost = pyo.Objective(
        expr=sum(get_val(cost, f) * model.x[f] for f in model.F),
        sense=pyo.minimize
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {'objective': obj_val, 'status': 'optimal'}