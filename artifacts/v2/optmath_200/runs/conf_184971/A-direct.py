import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    item_weights = params["item_weights"]
    container_capacity = params["container_capacity"]

    num_items = len(item_weights)
    num_containers = 7

    items = list(range(num_items))
    containers = list(range(num_containers))

    model = pyo.ConcreteModel()

    model.assign = pyo.Var(items, containers, domain=pyo.Binary)
    model.use = pyo.Var(containers, domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(mdl.use[c] for c in containers)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def capacity_rule(mdl, c):
        return sum(item_weights[i] * mdl.assign[i, c] for i in items) <= container_capacity * mdl.use[c]

    model.capacity_con = pyo.Constraint(containers, rule=capacity_rule)

    def assignment_rule(mdl, i):
        return sum(mdl.assign[i, c] for c in containers) == 1

    model.assignment_con = pyo.Constraint(items, rule=assignment_rule)

    def linking_rule(mdl, i, c):
        return mdl.assign[i, c] <= mdl.use[c]

    model.linking_con = pyo.Constraint(items, containers, rule=linking_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}