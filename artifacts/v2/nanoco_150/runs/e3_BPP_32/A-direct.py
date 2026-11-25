import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    spot_durations = list(params["spot_durations"])
    slot_capacity = params["slot_capacity"]

    n = len(spot_durations)
    T = n  # upper bound on number of slots

    model = pyo.ConcreteModel()

    model.SPOTS = pyo.RangeSet(0, n - 1)
    model.SLOTS = pyo.RangeSet(0, T - 1)

    model.x = pyo.Var(model.SPOTS, model.SLOTS, domain=pyo.Binary)
    model.y = pyo.Var(model.SLOTS, domain=pyo.Binary)

    def obj_rule(m):
        return sum(m.y[j] for j in m.SLOTS)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def assign_rule(m, i):
        return sum(m.x[i, j] for j in m.SLOTS) == 1

    model.assign_con = pyo.Constraint(model.SPOTS, rule=assign_rule)

    def cap_rule(m, j):
        return sum(spot_durations[i] * m.x[i, j] for i in m.SPOTS) <= slot_capacity * m.y[j]

    model.cap_con = pyo.Constraint(model.SLOTS, rule=cap_rule)

    # Symmetry breaking: enforce non-increasing "used" pattern
    def sym_rule(m, j):
        if j < T - 1:
            return m.y[j] >= m.y[j + 1]
        return pyo.Constraint.Skip

    model.sym_con = pyo.Constraint(model.SLOTS, rule=sym_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}