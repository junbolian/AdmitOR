import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["Eggs", "Grains", "Berries", "Nuts", "Salmon", "Vegetables", "Rice", "Meat"]

    cost_d = {f: params["cost"][i] for i, f in enumerate(foods)}
    protein_d = {f: params["protein"][i] for i, f in enumerate(foods)}
    carbs_d = {f: params["carbs"][i] for i, f in enumerate(foods)}
    calories_d = {f: params["calories"][i] for i, f in enumerate(foods)}

    protein_req = params["protein_req"]
    carb_req = params["carb_req"]
    calorie_req = params["calorie_req"]

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=foods, ordered=True)
    model.x = pyo.Var(model.F, domain=pyo.NonNegativeIntegers)

    def cost_rule(m):
        return sum(cost_d[f] * m.x[f] for f in m.F)

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    model.protein_con = pyo.Constraint(
        expr=sum(protein_d[f] * model.x[f] for f in model.F) >= protein_req
    )
    model.carb_con = pyo.Constraint(
        expr=sum(carbs_d[f] * model.x[f] for f in model.F) >= carb_req
    )
    model.calorie_con = pyo.Constraint(
        expr=sum(calories_d[f] * model.x[f] for f in model.F) >= calorie_req
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}