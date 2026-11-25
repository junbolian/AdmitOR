import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    processing_times = params["processing_times"]

    J = list(range(3))
    M = list(range(3))

    pt = {(j, k): processing_times[j][k] for j in J for k in M}

    bigM = sum(pt.values())

    model = pyo.ConcreteModel()

    # Disjunctive (precedence) binaries for each machine: seq[j1,j2,k] = 1 if j1 before j2 on machine k
    model.seq = pyo.Var(J, J, M, domain=pyo.Binary)
    # Completion time variables
    model.C = pyo.Var(J, M, domain=pyo.NonNegativeReals)
    # Makespan
    model.Cmax = pyo.Var(domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return m.Cmax
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # On each machine, for each pair j1 != j2: exactly one precedence
    def order_rule(m, j1, j2, k):
        if j1 == j2:
            return pyo.Constraint.Skip
        return m.seq[j1, j2, k] + m.seq[j2, j1, k] == 1
    model.order = pyo.Constraint(J, J, M, rule=order_rule)

    def pair_rule(m, j1, j2, k):
        if j1 == j2:
            return pyo.Constraint.Skip
        return m.C[j2, k] >= m.C[j1, k] + pt[j2, k] - bigM * (1 - m.seq[j1, j2, k])
    model.pair = pyo.Constraint(J, J, M, rule=pair_rule)

    # Makespan dominates all completion times
    def cmax_rule(m, j, k):
        return m.Cmax >= m.C[j, k]
    model.cmax_con = pyo.Constraint(J, M, rule=cmax_rule)

    # Time lag between consecutive operations of the same job (any sequence)
    # For each job, for each pair of machines, ensure correct ordering with time lags
    model.jobseq = pyo.Var(J, M, M, domain=pyo.Binary)

    # same-machine-no-overlap per job already in pair constraints; need per-job ordering across machines
    # For job j, machines k1 and k2: either C[j,k2] >= C[j,k1] + p[j,k2] or vice versa
    def jobseq_rule(m, j, k1, k2):
        if k1 >= k2:
            return pyo.Constraint.Skip
        return m.jobseq[j, k1, k2] + m.jobseq[j, k2, k1] == 1
    model.jobseq_con = pyo.Constraint(J, M, M, rule=jobseq_rule)

    def joborder_rule(m, j, k1, k2):
        if k1 == k2:
            return pyo.Constraint.Skip
        return m.C[j, k2] >= m.C[j, k1] + pt[j, k2] - bigM * (1 - m.jobseq[j, k1, k2])
    model.joborder = pyo.Constraint(J, M, M, rule=joborder_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}