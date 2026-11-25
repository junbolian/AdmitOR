import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    bin_capacity = params["bin_capacity"]
    item_weights = params["item_weights"]

    num_items = len(item_weights)
    # Structural bound: at most one bin per item (never more than num_items bins needed)
    num_bins = num_items

    model = pyo.ConcreteModel()

    model.ITEMS = pyo.RangeSet(0, num_items - 1)
    model.BINS = pyo.RangeSet(0, num_bins - 1)

    # Decision: y[b] = 1 if bin b is used
    model.y = pyo.Var(model.BINS, domain=pyo.Binary)
    # Decision: x[i, b] = 1 if item i is assigned to bin b
    model.x = pyo.Var(model.ITEMS, model.BINS, domain=pyo.Binary)

    # Objective: minimize number of bins used
    model.total_bins = pyo.Objective(
        expr=sum(model.y[b] for b in model.BINS), sense=pyo.minimize
    )

    # Each item assigned to exactly one bin
    def assign_rule(m, i):
        return sum(m.x[i, b] for b in m.BINS) == 1

    model.assign_con = pyo.Constraint(model.ITEMS, rule=assign_rule)

    # Capacity constraint per bin
    def capacity_rule(m, b):
        return sum(item_weights[i] * m.x[i, b] for i in m.ITEMS) <= bin_capacity * m.y[b]

    model.capacity_con = pyo.Constraint(model.BINS, rule=capacity_rule)

    # Linking: item can only be assigned to a bin if that bin is used
    def link_rule(m, i, b):
        return m.x[i, b] <= m.y[b]

    model.link_con = pyo.Constraint(model.ITEMS, model.BINS, rule=link_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_bins))
    return {"objective": obj_val, "status": "optimal"}