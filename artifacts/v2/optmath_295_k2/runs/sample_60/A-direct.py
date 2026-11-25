import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    weights = params["package_weights"]
    capacity = params["truck_capacity"]

    n_packages = len(weights)
    n_trucks = n_packages

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, n_packages - 1)
    model.T = pyo.RangeSet(0, n_trucks - 1)

    model.x = pyo.Var(model.P, model.T, domain=pyo.Binary)
    model.y = pyo.Var(model.T, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(model.y[t] for t in model.T),
        sense=pyo.minimize,
    )

    model.assign_once = pyo.Constraint(
        model.P,
        rule=lambda model, p: sum(model.x[p, t] for t in model.T) == 1,
    )

    model.capacity_con = pyo.Constraint(
        model.T,
        rule=lambda model, t: sum(weights[p] * model.x[p, t] for p in model.P)
        <= capacity * model.y[t],
    )

    model.link = pyo.Constraint(
        model.P, model.T,
        rule=lambda model, p, t: model.x[p, t] <= model.y[t],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}