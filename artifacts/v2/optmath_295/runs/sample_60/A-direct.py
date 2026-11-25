import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    weights = params["package_weights"]
    cap = params["truck_capacity"]
    num_trucks = params["num_trucks"]
    num_packages = params["num_packages"]

    P = range(num_packages)
    T = range(num_trucks)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(P, T, domain=pyo.Binary)
    model.y = pyo.Var(T, domain=pyo.Binary)

    model.obj = pyo.Objective(expr=sum(model.y[t] for t in T), sense=pyo.minimize)

    model.assign = pyo.Constraint(
        P, rule=lambda m, p: sum(m.x[p, t] for t in T) == 1
    )

    model.capacity = pyo.Constraint(
        T,
        rule=lambda m, t: sum(weights[p] * m.x[p, t] for p in P) <= cap * m.y[t],
    )

    model.linkage = pyo.Constraint(
        P, T, rule=lambda m, p, t: m.x[p, t] <= m.y[t]
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}