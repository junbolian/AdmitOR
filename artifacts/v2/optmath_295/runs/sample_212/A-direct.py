import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    resource_coeff = params["resource_coeff"]
    resource_limit = params["resource_limit"]
    capacity = params["capacity"]

    n = len(profit)
    item_ids = list(range(n))

    model = pyo.ConcreteModel()
    model.item_set = pyo.Set(initialize=item_ids)

    model.x = pyo.Var(model.item_set, within=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(profit[i] * m.x[i] for i in m.item_set)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def resource_rule(m):
        return sum(resource_coeff[i] * m.x[i] for i in m.item_set) <= resource_limit
    model.resource_con = pyo.Constraint(rule=resource_rule)

    def cap_rule(m, i):
        return m.x[i] <= capacity[i]
    model.cap_con = pyo.Constraint(model.item_set, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}