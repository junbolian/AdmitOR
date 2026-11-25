import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    bin_capacity = params["bin_capacity"]
    weights = [
        params["item_weight_0"],
        params["item_weight_1"],
        params["item_weight_2"],
        params["item_weight_3"],
        params["item_weight_4"],
        params["item_weight_5"],
        params["item_weight_6"],
    ]
    num_items = len(weights)
    num_bins = num_items  # worst case: one item per bin

    items = range(num_items)
    bins = range(num_bins)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(items, bins, domain=pyo.Binary)
    model.y = pyo.Var(bins, domain=pyo.Binary)

    model.obj = pyo.Objective(expr=sum(model.y[b] for b in bins), sense=pyo.minimize)

    model.assign_once = pyo.ConstraintList()
    for i in items:
        model.assign_once.add(sum(model.x[i, b] for b in bins) == 1)

    model.capacity = pyo.ConstraintList()
    for b in bins:
        model.capacity.add(sum(weights[i] * model.x[i, b] for i in items) <= bin_capacity * model.y[b])

    # Symmetry breaking: enforce that bins are used in order
    model.symmetry = pyo.ConstraintList()
    for b in range(num_bins - 1):
        model.symmetry.add(model.y[b] >= model.y[b + 1])

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}