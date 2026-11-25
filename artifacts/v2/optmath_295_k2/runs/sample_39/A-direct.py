import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    package_weights = params["package_weights"]
    capacity = params["truck_capacity"]
    num_trucks = params["num_trucks"]
    num_packages = len(package_weights)

    P = range(num_packages)
    T = range(num_trucks)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(P, T, domain=pyo.Binary)
    model.y = pyo.Var(T, domain=pyo.Binary)

    model.obj = pyo.Objective(expr=sum(model.y[t] for t in T), sense=pyo.minimize)

    def assign_rule(mdl, p):
        return sum(mdl.x[p, t] for t in T) == 1

    model.assign_con = pyo.Constraint(P, rule=assign_rule)

    def cap_rule(mdl, t):
        return sum(package_weights[p] * mdl.x[p, t] for p in P) <= capacity * mdl.y[t]

    model.cap_con = pyo.Constraint(T, rule=cap_rule)

    def link_rule(mdl, p, t):
        return mdl.x[p, t] <= mdl.y[t]

    model.link_con = pyo.Constraint(P, T, rule=link_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}