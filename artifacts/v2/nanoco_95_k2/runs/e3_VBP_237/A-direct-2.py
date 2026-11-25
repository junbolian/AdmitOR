import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacities = params["capacities"]
    weights = params["weights"]

    num_items = len(weights)
    num_dims = len(capacities)

    model = pyo.ConcreteModel()

    model.item_set = pyo.RangeSet(0, num_items - 1)
    model.dim_set = pyo.RangeSet(0, num_dims - 1)
    model.slot_set = pyo.RangeSet(0, num_items - 1)

    model.assigned = pyo.Var(model.item_set, model.slot_set, domain=pyo.Binary)
    model.active = pyo.Var(model.slot_set, domain=pyo.Binary)

    def rule_assign_once(m, i):
        return sum(m.assigned[i, j] for j in m.slot_set) == 1

    model.assign_once = pyo.Constraint(model.item_set, rule=rule_assign_once)

    def rule_capacity(m, j, d):
        return (
            sum(m.assigned[i, j] * weights[i][d] for i in m.item_set)
            <= capacities[d] * m.active[j]
        )

    model.capacity = pyo.Constraint(model.slot_set, model.dim_set, rule=rule_capacity)

    def rule_link(m, i, j):
        return m.assigned[i, j] <= m.active[j]

    model.link = pyo.Constraint(model.item_set, model.slot_set, rule=rule_link)

    def rule_obj(m):
        return sum(m.active[j] for j in m.slot_set)

    model.objective = pyo.Objective(rule=rule_obj, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.objective))

    return {"objective": obj_val, "status": "optimal"}