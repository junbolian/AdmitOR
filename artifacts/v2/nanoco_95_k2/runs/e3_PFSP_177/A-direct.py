import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    pt = params["proc_time"]
    n = len(pt)
    m = len(pt[0])

    model = pyo.ConcreteModel()

    model.POS = pyo.RangeSet(0, n - 1)
    model.BATCH = pyo.RangeSet(0, n - 1)
    model.UNIT = pyo.RangeSet(0, m - 1)

    # x[k, b] = 1 if batch b is scheduled at position k
    model.x = pyo.Var(model.POS, model.BATCH, domain=pyo.Binary)

    # Completion time of batch at position k on unit u
    model.C = pyo.Var(model.POS, model.UNIT, domain=pyo.NonNegativeReals)

    model.makespan = pyo.Var(domain=pyo.NonNegativeReals)

    # Each position gets exactly one batch
    def rule_assign_pos(mdl, k):
        return sum(mdl.x[k, b] for b in mdl.BATCH) == 1

    model.assign_pos = pyo.Constraint(model.POS, rule=rule_assign_pos)

    # Each batch assigned to exactly one position
    def rule_assign_batch(mdl, b):
        return sum(mdl.x[k, b] for k in mdl.POS) == 1

    model.assign_batch = pyo.Constraint(model.BATCH, rule=rule_assign_batch)

    # Completion time constraints
    def rule_c(mdl, k, u):
        p_k = sum(pt[b][u] * mdl.x[k, b] for b in mdl.BATCH)
        expr = mdl.C[k, u] >= p_k
        if u >= 1:
            expr = expr & (mdl.C[k, u] >= mdl.C[k, u - 1] + p_k)
        if k >= 1:
            expr = expr & (mdl.C[k, u] >= mdl.C[k - 1, u] + p_k)
        return expr

    model.c_comp = pyo.Constraint(model.POS, model.UNIT, rule=rule_c)

    def rule_mk(mdl, k):
        return mdl.makespan >= mdl.C[k, m - 1]

    model.c_mk = pyo.Constraint(model.POS, rule=rule_mk)

    model.obj = pyo.Objective(expr=model.makespan, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}