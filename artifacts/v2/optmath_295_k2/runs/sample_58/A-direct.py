import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    item_values = params["item_values"]
    item_weights = params["item_weights"]

    n = len(item_values)

    model = pyo.ConcreteModel()
    model.item_idx = pyo.RangeSet(0, n - 1)

    model.x = pyo.Var(model.item_idx, domain=pyo.Binary)

    def obj_rule(m):
        return sum(item_values[i] * m.x[i] for i in m.item_idx)

    model.profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def weight_rule(m):
        return sum(item_weights[i] * m.x[i] for i in m.item_idx) <= capacity

    model.weight_limit = pyo.Constraint(rule=weight_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}