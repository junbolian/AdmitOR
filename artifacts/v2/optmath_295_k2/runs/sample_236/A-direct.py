import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    items = list(range(7))
    weights = [
        params["item_weight_0"],
        params["item_weight_1"],
        params["item_weight_2"],
        params["item_weight_3"],
        params["item_weight_4"],
        params["item_weight_5"],
        params["item_weight_6"],
    ]
    capacity = params["bin_capacity"]

    n_bins = 7
    bins = list(range(n_bins))

    model = pyo.ConcreteModel()

    model.ITEMS = pyo.Set(initialize=items)
    model.BINS = pyo.Set(initialize=bins)

    model.y = pyo.Var(model.BINS, domain=pyo.Binary)
    model.x = pyo.Var(model.ITEMS, model.BINS, domain=pyo.Binary)

    def obj_rule(m):
        return sum(m.y[b] for b in m.BINS)

    model.total_bins = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def assign_rule(m, i):
        return sum(m.x[i, b] for b in m.BINS) == 1

    model.assign_con = pyo.Constraint(model.ITEMS, rule=assign_rule)

    def cap_rule(m, b):
        return sum(weights[i] * m.x[i, b] for i in m.ITEMS) <= capacity * m.y[b]

    model.cap_con = pyo.Constraint(model.BINS, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_bins))
    return {"objective": obj_val, "status": "optimal"}