import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    weights = params["item_weights"]
    capacity = params["bin_capacity"]

    items = list(range(len(weights)))
    bins = list(range(len(weights)))

    model = pyo.ConcreteModel()

    model.item_set = pyo.Set(initialize=items)
    model.bin_set = pyo.Set(initialize=bins)

    model.xy = pyo.Var(model.item_set, model.bin_set, domain=pyo.Binary)
    model.used = pyo.Var(model.bin_set, domain=pyo.Binary)

    def capacity_rule(mdl, b):
        return sum(weights[i] * mdl.xy[i, b] for i in mdl.item_set) <= capacity * mdl.used[b]

    model.capacity_con = pyo.Constraint(model.bin_set, rule=capacity_rule)

    def assign_rule(mdl, i):
        return sum(mdl.xy[i, b] for b in mdl.bin_set) == 1

    model.assign_con = pyo.Constraint(model.item_set, rule=assign_rule)

    def link_rule(mdl, i, b):
        return mdl.xy[i, b] <= mdl.used[b]

    model.link_con = pyo.Constraint(model.item_set, model.bin_set, rule=link_rule)

    model.obj = pyo.Objective(expr=sum(model.used[b] for b in model.bin_set), sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}