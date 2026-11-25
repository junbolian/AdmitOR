import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    p = params["p"]
    njobs = len(p)
    nmach = len(p[0])

    model = pyo.ConcreteModel()

    J = list(range(njobs))
    M = list(range(nmach))
    K = list(range(njobs))

    model.J = pyo.Set(initialize=J, ordered=True)
    model.M = pyo.Set(initialize=M, ordered=True)
    model.K = pyo.Set(initialize=K, ordered=True)

    # y[i,k] = 1 if job i is assigned to position k in the permutation
    model.y = pyo.Var(model.J, model.K, domain=pyo.Binary)

    # Start and completion time of the job at position k on machine mach
    model.S = pyo.Var(model.K, model.M, domain=pyo.NonNegativeReals)
    model.C = pyo.Var(model.K, model.M, domain=pyo.NonNegativeReals)

    # Each job exactly one position; each position exactly one job
    model.assign_job = pyo.Constraint(
        model.J, rule=lambda m, i: sum(m.y[i, k] for k in m.K) == 1
    )
    model.assign_pos = pyo.Constraint(
        model.K, rule=lambda m, k: sum(m.y[i, k] for i in m.J) == 1
    )

    # Processing time of the job at position k on machine mach
    def proc_expr(m, k, mach):
        return sum(m.y[i, k] * p[i][mach] for i in m.J)

    # Startup on previous machine: same job must finish prev machine first
    def start_prev_mach_rule(m, k, mach):
        if mach == 0:
            return pyo.Constraint.Skip
        return m.S[k, mach] >= m.C[k, mach - 1]
    model.start_prev_mach = pyo.Constraint(model.K, model.M, rule=start_prev_mach_rule)

    # Start after previous job on same machine
    def start_prev_job_rule(m, k, mach):
        if k == 0:
            return pyo.Constraint.Skip
        return m.S[k, mach] >= m.C[k - 1, mach]
    model.start_prev_job = pyo.Constraint(model.K, model.M, rule=start_prev_job_rule)

    # Completion = start + processing time
    def comp_rule(m, k, mach):
        return m.C[k, mach] == m.S[k, mach] + proc_expr(m, k, mach)
    model.comp = pyo.Constraint(model.K, model.M, rule=comp_rule)

    # Makespan
    model.makespan = pyo.Var(domain=pyo.NonNegativeReals)
    model.makespan_con = pyo.Constraint(
        expr=model.makespan >= model.C[njobs - 1, nmach - 1]
    )

    model.obj = pyo.Objective(expr=model.makespan, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}