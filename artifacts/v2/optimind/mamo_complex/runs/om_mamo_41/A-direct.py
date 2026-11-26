import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["chicken", "rice", "eggs", "broccoli", "lentils", "apples"]

    protein = {f: params["protein_" + f] for f in foods}
    carb = {f: params["carb_" + f] for f in foods}
    cal = {f: params["cal_" + f] for f in foods}
    cost = {f: params["cost_" + f] for f in foods}

    model = pyo.ConcreteModel()
    model.FOODS = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.FOODS, domain=pyo.NonNegativeIntegers)

    def protein_rule(m):
        return sum(protein[f] * m.x[f] for f in m.FOODS) >= params["req_protein"]

    def carb_rule(m):
        return sum(carb[f] * m.x[f] for f in m.FOODS) >= params["req_carbs"]

    def cal_rule(m):
        return sum(cal[f] * m.x[f] for f in m.FOODS) >= params["req_calories"]

    model.protein_con = pyo.Constraint(rule=protein_rule)
    model.carb_con = pyo.Constraint(rule=carb_rule)
    model.cal_con = pyo.Constraint(rule=cal_rule)

    model.total_cost = pyo.Objective(
        expr=sum(cost[f] * model.x[f] for f in model.FOODS),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}