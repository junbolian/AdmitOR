import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    values = params["values"]
    weights = params["weights"]
    capacity = params["capacity"]

    n = len(values)
    items = range(n)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(items, domain=pyo.Binary)

    def obj_rule(m):
        return sum(values[i] * m.x[i] for i in items)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def cap_rule(m):
        return sum(weights[i] * m.x[i] for i in items) <= capacity

    model.cap = pyo.Constraint(rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}