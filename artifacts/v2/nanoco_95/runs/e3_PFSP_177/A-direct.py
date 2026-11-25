import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    batches = ["B0", "B1", "B2", "B3"]
    units = ["U0", "U1", "U2"]
    n = len(batches)
    m = len(units)

    # processing_time is indexed [batch][unit]
    pt = params["processing_time"]
    p = [[pt[batches[b]][units[u]] for u in range(m)] for b in range(n)]

    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, n - 1)
    model.U = pyo.RangeSet(0, m - 1)
    model.B = pyo.RangeSet(0, n - 1)

    model.x = pyo.Var(model.I, model.B, domain=pyo.Binary)
    model.S = pyo.Var(model.I, model.U, domain=pyo.NonNegativeReals)
    model.C = pyo.Var(model.I, model.U, domain=pyo.NonNegativeReals)
    model.Cmax = pyo.Var(domain=pyo.NonNegativeReals)

    # Each position has exactly one batch
    def one_batch_per_pos_rule(model, i):
        return sum(model.x[i, b] for b in model.B) == 1

    model.one_batch_per_pos = pyo.Constraint(model.I, rule=one_batch_per_pos_rule)

    # Each batch occupies exactly one position
    def one_pos_per_batch_rule(model, b):
        return sum(model.x[i, b] for i in model.I) == 1

    model.one_pos_per_batch = pyo.Constraint(model.B, rule=one_pos_per_batch_rule)

    # Completion linked to start via position-dependent duration
    def complink_rule(model, i, u):
        dur = sum(p[b][u] * model.x[i, b] for b in model.B)
        return model.C[i, u] == model.S[i, u] + dur

    model.complink = pyo.Constraint(model.I, model.U, rule=complink_rule)

    # Flow within a batch: no overlap across units
    def flow_rule(model, i, u):
        if u < m - 1:
            return model.S[i, u + 1] >= model.C[i, u]
        return pyo.Constraint.Skip

    model.flow = pyo.Constraint(model.I, model.U, rule=flow_rule)

    # Machine capacity: consecutive positions don't overlap at each unit
    def machine_rule(model, i, u):
        if i < n - 1:
            return model.S[i + 1, u] >= model.C[i, u]
        return pyo.Constraint.Skip

    model.machine = pyo.Constraint(model.I, model.U, rule=machine_rule)

    # Makespan
    def cmax_rule(model, i):
        return model.Cmax >= model.C[i, m - 1]

    model.cmax = pyo.Constraint(model.I, rule=cmax_rule)

    model.obj = pyo.Objective(expr=model.Cmax, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}