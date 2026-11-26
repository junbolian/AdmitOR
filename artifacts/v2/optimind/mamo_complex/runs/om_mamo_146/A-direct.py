import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    foods = ["chicken", "pasta", "apples", "tuna", "rice"]

    model = pyo.ConcreteModel()

    model.foods = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.foods, domain=pyo.NonNegativeIntegers)

    cost = {f: params["cost_" + f] for f in foods}
    protein = {f: params["protein_" + f] for f in foods}
    carbs = {f: params["carbs_" + f] for f in foods}
    calories = {f: params["calories_" + f] for f in foods}

    model.protein_req = pyo.Constraint(
        expr=sum(protein[f] * model.x[f] for f in model.foods) >= params["protein_req"]
    )
    model.carbs_req = pyo.Constraint(
        expr=sum(carbs[f] * model.x[f] for f in model.foods) >= params["carbs_req"]
    )
    model.calories_req = pyo.Constraint(
        expr=sum(calories[f] * model.x[f] for f in model.foods) >= params["calories_req"]
    )

    model.total_cost = pyo.Objective(
        expr=sum(cost[f] * model.x[f] for f in model.foods), sense=pyo.minimize
    )

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}