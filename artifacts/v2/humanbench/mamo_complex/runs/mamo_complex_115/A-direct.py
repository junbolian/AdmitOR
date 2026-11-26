import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    foods = ["chicken", "rice", "tuna", "beef", "corn", "whey"]

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.F, domain=pyo.NonNegativeReals)

    protein = {f: params["protein_" + f] for f in foods}
    carbs = {f: params["carbs_" + f] for f in foods}
    calories = {f: params["calories_" + f] for f in foods}
    cost = {f: params["cost_" + f] for f in foods}

    model.protein_con = pyo.Constraint(
        expr=sum(protein[f] * model.x[f] for f in model.F) >= params["target_protein"]
    )
    model.carbs_con = pyo.Constraint(
        expr=sum(carbs[f] * model.x[f] for f in model.F) >= params["target_carbs"]
    )
    model.calories_con = pyo.Constraint(
        expr=sum(calories[f] * model.x[f] for f in model.F) >= params["target_calories"]
    )

    model.cost_obj = pyo.Objective(
        expr=sum(cost[f] * model.x[f] for f in model.F), sense=pyo.minimize
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.cost_obj))
    return {"objective": obj_val, "status": "optimal"}