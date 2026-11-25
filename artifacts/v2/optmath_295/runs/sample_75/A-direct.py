import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    resource_use = params["resource_use"]
    resource_budget = params["resource_budget"]
    capacity = params["capacity"]

    n = len(profit)
    idx = list(range(n))

    model = pyo.ConcreteModel()

    model.item_set = pyo.Set(initialize=idx)

    model.x = pyo.Var(model.item_set, bounds=(0, None))

    def cap_rule(m, i):
        return m.x[i] <= capacity[i]
    model.cap_con = pyo.Constraint(model.item_set, rule=cap_rule)

    def resource_rule(m):
        return sum(resource_use[i] * m.x[i] for i in m.item_set) <= resource_budget
    model.resource_con = pyo.Constraint(rule=resource_rule)

    def obj_rule(m):
        return sum(profit[i] * m.x[i] for i in m.item_set)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}