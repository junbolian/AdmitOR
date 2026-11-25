import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    weights = params["resource_weights"]
    cap = params["center_capacity"]

    resources = list(range(len(weights)))
    centers = list(range(len(weights)))

    model = pyo.ConcreteModel()
    model.R = pyo.Set(initialize=resources)
    model.C = pyo.Set(initialize=centers)

    model.x = pyo.Var(model.R, model.C, domain=pyo.Binary)
    model.y = pyo.Var(model.C, domain=pyo.Binary)

    def assign_rule(mdl, r):
        return sum(mdl.x[r, c] for c in mdl.C) == 1
    model.assign_con = pyo.Constraint(model.R, rule=assign_rule)

    def cap_rule(mdl, c):
        return sum(weights[r] * mdl.x[r, c] for r in mdl.R) <= cap * mdl.y[c]
    model.cap_con = pyo.Constraint(model.C, rule=cap_rule)

    model.obj = pyo.Objective(expr=sum(model.y[c] for c in model.C), sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}