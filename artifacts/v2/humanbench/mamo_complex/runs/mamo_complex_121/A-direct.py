import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    foods = ["Chicken", "Rice", "Beans", "Broccoli", "Fruit"]
    protein = {f: params["protein_content"][i] for i, f in enumerate(foods)}
    carbs = {f: params["carb_content"][i] for i, f in enumerate(foods)}
    calories = {f: params["calorie_content"][i] for i, f in enumerate(foods)}
    cost = {f: params["cost"][i] for i, f in enumerate(foods)}

    model = pyo.ConcreteModel()
    model.F = pyo.Set(initialize=foods)
    model.x = pyo.Var(model.F, domain=pyo.NonNegativeReals)

    model.protein_con = pyo.Constraint(
        expr=sum(protein[f] * model.x[f] for f in model.F) >= params["protein_requirement"]
    )
    model.carb_con = pyo.Constraint(
        expr=sum(carbs[f] * model.x[f] for f in model.F) >= params["carb_requirement"]
    )
    model.calorie_con = pyo.Constraint(
        expr=sum(calories[f] * model.x[f] for f in model.F) >= params["calorie_requirement"]
    )

    model.total_cost = pyo.Objective(
        expr=sum(cost[f] * model.x[f] for f in model.F), sense=pyo.minimize
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible or failed"}