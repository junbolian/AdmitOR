import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    weights = params["package_weights"]
    capacity = params["truck_capacity"]

    n_packages = len(weights)
    n_trucks = n_packages

    packages = range(n_packages)
    trucks = range(n_trucks)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(packages, trucks, domain=pyo.Binary)
    model.y = pyo.Var(trucks, domain=pyo.Binary)

    def obj_rule(m):
        return sum(m.y[t] for t in trucks)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def assign_rule(m, p):
        return sum(m.x[p, t] for t in trucks) == 1

    model.assign = pyo.Constraint(packages, rule=assign_rule)

    def cap_rule(m, t):
        return sum(weights[p] * m.x[p, t] for p in packages) <= capacity * m.y[t]

    model.cap = pyo.Constraint(trucks, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}