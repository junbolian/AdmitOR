import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    values = params["values"]
    weights = params["weights"]

    n = len(values)
    index_set = list(range(n))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(index_set, domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(values[i] * mdl.x[i] for i in index_set)

    model.total_value = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def weight_rule(mdl):
        return sum(weights[i] * mdl.x[i] for i in index_set) <= capacity

    model.capacity_constraint = pyo.Constraint(rule=weight_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_value))
    return {"objective": obj_val, "status": "optimal"}