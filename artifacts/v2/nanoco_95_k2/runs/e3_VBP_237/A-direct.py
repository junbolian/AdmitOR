import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacities = params["capacities"]
    weights = params["weights"]

    num_items = len(weights)
    num_dims = len(capacities)

    # Upper bound on the number of slots (worst case: one item per slot)
    max_slots = num_items

    model = pyo.ConcreteModel()

    model.ITEMS = pyo.RangeSet(0, num_items - 1)
    model.SLOTS = pyo.RangeSet(0, max_slots - 1)
    model.DIMS = pyo.RangeSet(0, num_dims - 1)

    # x[i, s] = 1 if item i assigned to slot s
    model.x = pyo.Var(model.ITEMS, model.SLOTS, domain=pyo.Binary)

    # y[s] = 1 if slot s is used
    model.y = pyo.Var(model.SLOTS, domain=pyo.Binary)

    # Objective: minimize the number of used slots
    def obj_rule(m):
        return sum(m.y[s] for s in m.SLOTS)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each item must be assigned to exactly one slot
    def assign_rule(m, i):
        return sum(m.x[i, s] for s in m.SLOTS) == 1

    model.assign_con = pyo.Constraint(model.ITEMS, rule=assign_rule)

    # Capacity constraints per slot per dimension
    def cap_rule(m, s, d):
        return sum(weights[i][d] * m.x[i, s] for i in m.ITEMS) <= capacities[d] * m.y[s]

    model.cap_con = pyo.Constraint(model.SLOTS, model.DIMS, rule=cap_rule)

    # Symmetry breaking: slot s can only be used if slot s-1 is used
    def sym_rule(m, s):
        if s == 0:
            return pyo.Constraint.Skip
        return m.y[s] <= m.y[s - 1]

    model.sym_con = pyo.Constraint(model.SLOTS, rule=sym_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}