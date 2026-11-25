import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    avail = params["avail"]
    time = params["time"]
    minProd = params["minProd"]
    maxProd = params["maxProd"]

    n_products = len(profit)
    n_stages = len(avail)

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, n_products - 1)
    model.S = pyo.RangeSet(0, n_stages - 1)

    model.x = pyo.Var(model.P, within=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(profit[i] * model.x[i] for i in model.P),
        sense=pyo.maximize,
    )

    def stage_rule(mdl, s):
        row = time[s]
        return sum(row[i] * mdl.x[i] for i in mdl.P) <= avail[s]

    model.stage_limit = pyo.Constraint(model.S, rule=stage_rule)

    def min_rule(mdl, i):
        return mdl.x[i] >= minProd[i]

    def max_rule(mdl, i):
        return mdl.x[i] <= maxProd[i]

    model.min_limit = pyo.Constraint(model.P, rule=min_rule)
    model.max_limit = pyo.Constraint(model.P, rule=max_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}