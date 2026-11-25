import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    weights = params["package_weights"]
    capacity = params["truck_capacity"]
    num_trucks = int(params["num_trucks"])

    packages = list(range(len(weights)))
    trucks = list(range(num_trucks))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=packages)
    model.T = pyo.Set(initialize=trucks)

    model.x = pyo.Var(model.P, model.T, domain=pyo.Binary)
    model.y = pyo.Var(model.T, domain=pyo.Binary)

    model.weight = pyo.Param(model.P, initialize={i: weights[i] for i in packages})

    model.obj = pyo.Objective(expr=sum(model.y[t] for t in model.T), sense=pyo.minimize)

    model.assign = pyo.Constraint(
        model.P, rule=lambda m, p: sum(m.x[p, t] for t in m.T) == 1
    )

    model.capacity = pyo.Constraint(
        model.T,
        rule=lambda m, t: sum(m.weight[p] * m.x[p, t] for p in m.P) <= capacity * m.y[t],
    )

    model.link = pyo.Constraint(
        model.P, model.T, rule=lambda m, p, t: m.x[p, t] <= m.y[t]
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}