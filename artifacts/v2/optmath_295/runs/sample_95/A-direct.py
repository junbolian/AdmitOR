import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = 9

    values = [params[f"value_{i}"] for i in range(n)]
    weights = [params[f"weight_{i}"] for i in range(n)]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.S = pyo.RangeSet(0, n - 1)

    model.x = pyo.Var(model.S, domain=pyo.Binary)

    def weight_rule(m):
        return sum(weights[i] * m.x[i] for i in m.S) <= capacity

    model.weight_con = pyo.Constraint(rule=weight_rule)

    def obj_rule(m):
        return sum(values[i] * m.x[i] for i in m.S)

    model.total_value = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_value))
    return {"objective": obj_val, "status": "optimal"}