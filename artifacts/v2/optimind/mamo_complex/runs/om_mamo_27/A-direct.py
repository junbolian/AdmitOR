import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["bread", "milk", "fish", "potato"]

    model = pyo.ConcreteModel()

    model.FOOD = pyo.Set(initialize=foods)

    protein = {f: params["protein_" + f] for f in foods}
    carb = {f: params["carb_" + f] for f in foods}
    cal = {f: params["cal_" + f] for f in foods}
    cost = {f: params["cost_" + f] for f in foods}

    model.x = pyo.Var(model.FOOD, domain=pyo.NonNegativeReals)

    model.protein_con = pyo.Constraint(
        expr=sum(protein[f] * model.x[f] for f in foods) >= params["req_protein"]
    )
    model.carb_con = pyo.Constraint(
        expr=sum(carb[f] * model.x[f] for f in foods) >= params["req_carb"]
    )
    model.cal_con = pyo.Constraint(
        expr=sum(cal[f] * model.x[f] for f in foods) >= params["req_cal"]
    )

    model.cost_obj = pyo.Objective(
        expr=sum(cost[f] * model.x[f] for f in foods), sense=pyo.minimize
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.cost_obj))
    return {"objective": obj_val, "status": "optimal"}