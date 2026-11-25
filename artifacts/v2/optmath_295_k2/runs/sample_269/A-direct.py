import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    resource_consumption = params["resource_consumption"]
    total_resource = params["total_resource"]
    capacity = params["capacity"]

    n = len(profit)
    items = range(n)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(items, domain=pyo.NonNegativeReals)

    def cap_rule(mdl, i):
        return mdl.x[i] <= capacity[i]

    model.cap_con = pyo.Constraint(items, rule=cap_rule)

    def res_rule(mdl):
        return sum(resource_consumption[i] * mdl.x[i] for i in items) <= total_resource

    model.res_con = pyo.Constraint(rule=res_rule)

    model.obj = pyo.Objective(
        expr=sum(profit[i] * model.x[i] for i in items),
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}