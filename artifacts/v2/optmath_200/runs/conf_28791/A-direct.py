import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    bin_capacity = params["bin_capacity"]
    item_weights = params["item_weights"]

    n_items = len(item_weights)
    n_bins = n_items

    items = range(n_items)
    bins = range(n_bins)

    model = pyo.ConcreteModel()
    model.x = pyo.Var(items, bins, domain=pyo.Binary)
    model.y = pyo.Var(bins, domain=pyo.Binary)
    model.obj = pyo.Objective(
        expr=sum(model.y[j] for j in bins), sense=pyo.minimize
    )
    model.assign = pyo.Constraint(
        items, rule=lambda m, i: sum(m.x[i, j] for j in bins) == 1
    )
    model.capacity = pyo.Constraint(
        bins,
        rule=lambda m, j: sum(item_weights[i] * m.x[i, j] for i in items)
        <= bin_capacity * m.y[j],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}