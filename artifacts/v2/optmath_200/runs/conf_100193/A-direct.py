import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    value_A = params["value_A"]
    value_B = params["value_B"]
    value_C = params["value_C"]
    weight_A = params["weight_A"]
    weight_B = params["weight_B"]
    weight_C = params["weight_C"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.CROPS = pyo.Set(initialize=["A", "B", "C"])

    values = {"A": value_A, "B": value_B, "C": value_C}
    weights = {"A": weight_A, "B": weight_B, "C": weight_C}

    model.x = pyo.Var(model.CROPS, domain=pyo.Binary)

    def obj_rule(m):
        return sum(values[c] * m.x[c] for c in m.CROPS)

    model.profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def weight_rule(m):
        return sum(weights[c] * m.x[c] for c in m.CROPS) <= capacity

    model.weight_con = pyo.Constraint(rule=weight_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}