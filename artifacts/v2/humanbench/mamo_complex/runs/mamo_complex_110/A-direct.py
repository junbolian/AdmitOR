import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["eggs", "rice", "chicken", "broccoli"]

    cost = {f: params["cost_" + f] for f in foods}
    protein = {f: params["protein_" + f] for f in foods}
    carbs = {f: params["carbs_" + f] for f in foods}
    cal = {f: params["cal_" + f] for f in foods}

    model = pyo.ConcreteModel()

    model.x = pyo.Var(foods, domain=pyo.NonNegativeReals)

    model.protein_con = pyo.Constraint(
        expr=sum(protein[f] * model.x[f] for f in foods) >= params["req_protein"]
    )
    model.carbs_con = pyo.Constraint(
        expr=sum(carbs[f] * model.x[f] for f in foods) >= params["req_carbs"]
    )
    model.cal_con = pyo.Constraint(
        expr=sum(cal[f] * model.x[f] for f in foods) >= params["req_cal"]
    )

    model.total_cost = pyo.Objective(
        expr=sum(cost[f] * model.x[f] for f in foods), sense=pyo.minimize
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}