import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    foods = ["lentils", "rice", "chicken", "beef", "tofu"]

    cost = {f: params[f"cost_{f}"] for f in foods}
    protein = {f: params[f"protein_{f}"] for f in foods}
    carbs = {f: params[f"carbs_{f}"] for f in foods}
    calories = {f: params[f"calories_{f}"] for f in foods}

    model = pyo.ConcreteModel()
    model.F = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.F, domain=pyo.NonNegativeReals)
    model.total_cost = pyo.Objective(
        expr=sum(cost[f] * model.x[f] for f in model.F),
        sense=pyo.minimize,
    )

    model.protein_con = pyo.Constraint(
        expr=sum(protein[f] * model.x[f] for f in model.F) >= params["protein_req"]
    )
    model.carbs_con = pyo.Constraint(
        expr=sum(carbs[f] * model.x[f] for f in model.F) >= params["carbs_req"]
    )
    model.calorie_con = pyo.Constraint(
        expr=sum(calories[f] * model.x[f] for f in model.F) >= params["calorie_req"]
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}