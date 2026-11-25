import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["bin_capacity"]
    weights = params["item_weights"]

    items = list(range(len(weights)))
    bins = list(range(len(weights)))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(items, bins, domain=pyo.Binary)
    model.y = pyo.Var(bins, domain=pyo.Binary)

    model.assign = pyo.Constraint(
        items,
        rule=lambda m, i: sum(m.x[i, j] for j in bins) == 1,
    )

    model.capacity = pyo.Constraint(
        bins,
        rule=lambda m, j: sum(weights[i] * m.x[i, j] for i in items)
        <= capacity * m.y[j],
    )

    model.obj = pyo.Objective(
        expr=sum(model.y[j] for j in bins),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}