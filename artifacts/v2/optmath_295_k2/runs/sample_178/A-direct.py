import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    weights = params["supply_weights"]
    capacity = params["hospital_capacity"]

    supplies = list(range(len(weights)))
    hospitals = list(range(len(weights)))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(supplies, hospitals, domain=pyo.Binary)
    model.y = pyo.Var(hospitals, domain=pyo.Binary)

    def obj_rule(m):
        return sum(m.y[j] for j in hospitals)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def assign_rule(m, i):
        return sum(m.x[i, j] for j in hospitals) == 1

    model.assign = pyo.Constraint(supplies, rule=assign_rule)

    def cap_rule(m, j):
        return sum(weights[i] * m.x[i, j] for i in supplies) <= capacity * m.y[j]

    model.cap = pyo.Constraint(hospitals, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}