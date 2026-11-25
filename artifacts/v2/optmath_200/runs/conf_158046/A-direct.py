import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    resource_coeff = params["resource_coeff"]
    resource_total = params["resource_total"]
    capacity = params["capacity"]

    n = len(profit)
    items = list(range(n))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(items, domain=pyo.NonNegativeReals)

    def cap_rule(model, i):
        return model.x[i] <= capacity[i]

    model.cap_con = pyo.Constraint(items, rule=cap_rule)

    def res_rule(model):
        return sum(resource_coeff[i] * model.x[i] for i in items) <= resource_total

    model.res_con = pyo.Constraint(rule=res_rule)

    def obj_rule(model):
        return sum(profit[i] * model.x[i] for i in items)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}