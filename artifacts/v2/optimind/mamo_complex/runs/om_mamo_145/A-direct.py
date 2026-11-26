import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["eggs", "rice", "chicken", "broccoli"]

    model = pyo.ConcreteModel()
    model.x = pyo.Var(foods, domain=pyo.NonNegativeIntegers)

    protein = {f: params["protein_" + f] for f in foods}
    carb = {f: params["carb_" + f] for f in foods}
    cal = {f: params["cal_" + f] for f in foods}
    cost = {f: params["cost_" + f] for f in foods}

    model.protein_con = pyo.Constraint(
        expr=sum(protein[f] * model.x[f] for f in foods) >= params["protein_req"]
    )
    model.carb_con = pyo.Constraint(
        expr=sum(carb[f] * model.x[f] for f in foods) >= params["carb_req"]
    )
    model.cal_con = pyo.Constraint(
        expr=sum(cal[f] * model.x[f] for f in foods) >= params["cal_req"]
    )

    model.cost_obj = pyo.Objective(
        expr=sum(cost[f] * model.x[f] for f in foods), sense=pyo.minimize
    )

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.cost_obj))
    return {"objective": obj_val, "status": "optimal"}