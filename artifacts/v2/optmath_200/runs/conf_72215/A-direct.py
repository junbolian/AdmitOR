import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cap = params["bin_capacity"]
    weights = params["item_weights"]
    num_bins = int(params["num_bins"])
    num_items = int(params["num_items"])

    items = list(range(num_items))
    bins = list(range(num_bins))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(bins, items, domain=pyo.Binary)
    model.y = pyo.Var(bins, domain=pyo.Binary)

    model.obj = pyo.Objective(expr=sum(model.y[b] for b in bins), sense=pyo.minimize)

    model.assign_con = pyo.Constraint(
        items,
        rule=lambda mdl, i: sum(mdl.x[b, i] for b in bins) == 1,
    )

    model.cap_con = pyo.Constraint(
        bins,
        rule=lambda mdl, b: sum(weights[i] * mdl.x[b, i] for i in items)
        <= cap * mdl.y[b],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}