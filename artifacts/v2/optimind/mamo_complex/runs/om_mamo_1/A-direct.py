import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["chicken", "rice", "broccoli", "tofu", "beans"]

    cost = {f: params["cost_" + f] for f in foods}
    protein = {f: params["protein_" + f] for f in foods}
    carb = {f: params["carb_" + f] for f in foods}
    cal = {f: params["cal_" + f] for f in foods}

    model = pyo.ConcreteModel()
    model.F = pyo.Set(initialize=foods, ordered=True)

    model.x = pyo.Var(model.F, within=pyo.NonNegativeIntegers)

    model.cost_expr = sum(cost[f] * model.x[f] for f in model.F)

    model.protein_con = pyo.Constraint(
        expr=sum(protein[f] * model.x[f] for f in model.F) >= params["req_protein"]
    )
    model.carb_con = pyo.Constraint(
        expr=sum(carb[f] * model.x[f] for f in model.F) >= params["req_carb"]
    )
    model.cal_con = pyo.Constraint(
        expr=sum(cal[f] * model.x[f] for f in model.F) >= params["req_cal"]
    )

    model.obj = pyo.Objective(expr=model.cost_expr, sense=pyo.minimize)

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible or no solution"}

    return {"objective": obj_val, "status": "optimal"}