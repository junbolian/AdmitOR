import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    J = ["J0", "J1", "J2"]
    M = ["M0", "M1", "M2"]
    O = [(j, k) for j in J for k in M]

    p = {}
    for j in J:
        for k in M:
            p[(j, k)] = params["p_{}_{}".format(j, k)]

    model = pyo.ConcreteModel()

    model.Jset = pyo.Set(initialize=J)
    model.Mset = pyo.Set(initialize=M)
    model.Oset = pyo.Set(initialize=O, dimen=2)

    # Bit-variable for machine ordering: yM[(k, j1, j2)] == 1 means j1 precedes j2 on machine k
    model.yM = pyo.Var(model.Mset, model.Jset, model.Jset, domain=pyo.Binary)
    # Bit-variable for job ordering: yJ[(j, k1, k2)] == 1 means k1 precedes k2 for job j
    model.yJ = pyo.Var(model.Jset, model.Mset, model.Mset, domain=pyo.Binary)

    bigM = sum(p.values())

    model.x = pyo.Var(model.Oset, domain=pyo.NonNegativeReals)
    model.Cmax = pyo.Var(domain=pyo.NonNegativeReals)

    model.Cmax_con = pyo.Constraint(
        expr=model.Cmax >= sum(
            (model.x[j, k] + p[(j, k)]) for (j, k) in O
        )
    )

    # Fix: Cmax must be >= each completion time (use individual constraints)
    def cmax_each_rule(m, j, k):
        return m.Cmax >= m.x[j, k] + p[(j, k)]
    model.cmax_each = pyo.Constraint(model.Jset, model.Mset, rule=cmax_each_rule)

    # Remove the sum-based constraint (incorrect); rebuild with proper element constraints
    del model.Cmax_con

    # Machine disjunctive: for k, ordered pairs j1 < j2
    def mach_fwd_rule(m, k, j1, j2):
        return m.x[j1, k] + p[(j1, k)] <= m.x[j2, k] + bigM * m.yM[k, j1, j2]
    def mach_rev_rule(m, k, j1, j2):
        return m.x[j2, k] + p[(j2, k)] <= m.x[j1, k] + bigM * (1 - m.yM[k, j1, j2])

    mach_pairs = [(j1, j2) for i, j1 in enumerate(J) for j2 in J[i+1:]]
    model.MPairs = pyo.Set(initialize=mach_pairs, dimen=2)
    model.mach_fwd = pyo.Constraint(model.Mset, model.MPairs, rule=mach_fwd_rule)
    model.mach_rev = pyo.Constraint(model.Mset, model.MPairs, rule=mach_rev_rule)

    # Job disjunctive: for j, ordered pairs k1 < k2
    def job_fwd_rule(m, j, k1, k2):
        return m.x[j, k1] + p[(j, k1)] <= m.x[j, k2] + bigM * m.yJ[j, k1, k2]
    def job_rev_rule(m, j, k1, k2):
        return m.x[j, k2] + p[(j, k2)] <= m.x[j, k1] + bigM * (1 - m.yJ[j, k1, k2])

    tool_pairs = [(k1, k2) for i, k1 in enumerate(M) for k2 in M[i+1:]]
    model.TPairs = pyo.Set(initialize=tool_pairs, dimen=2)
    model.job_fwd = pyo.Constraint(model.Jset, model.TPairs, rule=job_fwd_rule)
    model.job_rev = pyo.Constraint(model.Jset, model.TPairs, rule=job_rev_rule)

    model.obj = pyo.Objective(expr=model.Cmax, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}