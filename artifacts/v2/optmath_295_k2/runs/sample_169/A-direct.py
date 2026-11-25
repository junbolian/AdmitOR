import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    values = params["values"]
    weights = params["weights"]

    n = len(values)
    items = list(range(n))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(items, domain=pyo.Binary)

    def obj_rule(m):
        return sum(values[i] * m.x[i] for i in items)

    model.total_value = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def cap_rule(m):
        return sum(weights[i] * m.x[i] for i in items) <= capacity

    model.weight_limit = pyo.Constraint(rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_value))
    return {"objective": obj_val, "status": "optimal"}