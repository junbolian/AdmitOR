import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    weights = params["weights"]

    num_dims = len(capacity)
    num_items = len(weights)
    num_slots = num_items  # upper bound on slots needed

    model = pyo.ConcreteModel()

    item_ids = list(range(num_items))
    slot_ids = list(range(num_slots))
    dim_ids = list(range(num_dims))

    # y[s] = 1 if slot s is used
    model.y = pyo.Var(slot_ids, domain=pyo.Binary)
    # x[i, s] = 1 if item i is assigned to slot s
    model.x = pyo.Var(item_ids, slot_ids, domain=pyo.Binary)

    def assign_rule(m, i):
        return sum(m.x[i, s] for s in slot_ids) == 1

    model.assign = pyo.Constraint(item_ids, rule=assign_rule)

    def cap_rule(m, s, d):
        return sum(weights[i][d] * m.x[i, s] for i in item_ids) <= capacity[d] * m.y[s]

    model.cap = pyo.Constraint(slot_ids, dim_ids, rule=cap_rule)

    def sym_rule(m, s):
        if s == 0:
            return pyo.Constraint.Skip
        return m.y[s] <= m.y[s - 1]

    model.sym = pyo.Constraint(slot_ids, rule=sym_rule)

    def obj_rule(m):
        return sum(m.y[s] for s in slot_ids)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}