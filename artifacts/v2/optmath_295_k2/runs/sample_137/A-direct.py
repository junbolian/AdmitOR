import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    avail = params["avail"]
    time = params["time"]
    minProd = params["minProd"]
    maxProd = params["maxProd"]

    n_products = 6
    n_stages = 11

    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, n_products - 1)
    model.stages = pyo.RangeSet(0, n_stages - 1)

    model.x = pyo.Var(model.products, within=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(profit[i] * m.x[i] for i in m.products)

    model.profit_obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def stage_rule(m, j):
        return sum(float(time[j * n_products + i]) * m.x[i] for i in m.products) <= avail[j]

    model.stage_limit = pyo.Constraint(model.stages, rule=stage_rule)

    def min_rule(m, i):
        return m.x[i] >= minProd[i]

    model.min_constraint = pyo.Constraint(model.products, rule=min_rule)

    def max_rule(m, i):
        return m.x[i] <= maxProd[i]

    model.max_constraint = pyo.Constraint(model.products, rule=max_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.profit_obj))

    return {"objective": obj_val, "status": "optimal"}