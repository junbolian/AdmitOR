import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    profit = params["profit"]
    resource_rate = params["resource_rate"]
    resource_capacity = params["resource_capacity"]
    production_limit = params["production_limit"]

    n = len(profit)
    items = list(range(n))

    model = pyo.ConcreteModel()
    model.x = pyo.Var(items, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(profit[i] * m.x[i] for i in items)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def resource_rule(m):
        return sum(resource_rate[i] * m.x[i] for i in items) <= resource_capacity
    model.resource_con = pyo.Constraint(rule=resource_rule)

    def limit_rule(m, i):
        return m.x[i] <= production_limit[i]
    model.limit_con = pyo.Constraint(items, rule=limit_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}