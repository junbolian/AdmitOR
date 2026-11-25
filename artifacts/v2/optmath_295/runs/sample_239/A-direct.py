import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    value = {
        0: params["value_item0"],
        1: params["value_item1"],
        2: params["value_item2"],
    }
    weight = {
        0: params["weight_item0"],
        1: params["weight_item1"],
        2: params["weight_item2"],
    }
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.ITEMS = pyo.Set(initialize=[0, 1, 2])

    model.select = pyo.Var(model.ITEMS, domain=pyo.Binary)

    def objective_rule(m):
        return sum(value[i] * m.select[i] for i in m.ITEMS)

    model.total_value = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    def weight_rule(m):
        return sum(weight[i] * m.select[i] for i in m.ITEMS) <= capacity

    model.weight_limit = pyo.Constraint(rule=weight_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_value))
    return {"objective": obj_val, "status": "optimal"}