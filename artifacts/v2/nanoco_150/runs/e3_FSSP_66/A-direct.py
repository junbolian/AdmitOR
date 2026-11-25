import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    pt = params["processing_times"]
    n_jobs = len(pt)          # 3 jobs
    n_mach = len(pt[0])       # 3 workstations

    model = pyo.ConcreteModel()

    model.JOBS = pyo.RangeSet(0, n_jobs - 1)
    model.MACHS = pyo.RangeSet(0, n_mach - 1)

    # Start time of job j on machine m
    model.start = pyo.Var(model.JOBS, model.MACHS, within=pyo.NonNegativeReals)
    # Completion time (makespan) of the whole line
    model.Cmax = pyo.Var(within=pyo.NonNegativeReals)

    # Disjunctive binary: y[j,k,m] = 1 if job j precedes job k on machine m
    # Only defined for j < k to avoid redundancy
    model.pairs = pyo.Set(initialize=[
        (j, k) for j in range(n_jobs) for k in range(n_jobs) if j < k
    ])
    model.y = pyo.Var(model.pairs, model.MACHS, within=pyo.Binary)

    bigM = sum(pt[j][m] for j in range(n_jobs) for m in range(n_mach))

    # Precedence constraints: job must finish on machine m before starting on m+1
    def prec_rule(model, j, m):
        if m < n_mach - 1:
            return model.start[j, m + 1] >= model.start[j, m] + pt[j][m]
        return pyo.Constraint.Skip
    model.prec = pyo.Constraint(model.JOBS, model.MACHS, rule=prec_rule)

    # Disjunctive constraints: no two jobs on same machine at same time
    def disj_rule(model, j, k, m):
        return model.start[k, m] >= model.start[j, m] + pt[j][m] - bigM * (1 - model.y[j, k, m])
    model.disj1 = pyo.Constraint(model.pairs, model.MACHS, rule=disj_rule)

    def disj_rule2(model, j, k, m):
        return model.start[j, m] >= model.start[k, m] + pt[k][m] - bigM * model.y[j, k, m]
    model.disj2 = pyo.Constraint(model.pairs, model.MACHS, rule=disj_rule2)

    # Makespan: completion time on last machine for every job
    def cmax_rule(model, j):
        return model.Cmax >= model.start[j, n_mach - 1] + pt[j][n_mach - 1]
    model.cmax_con = pyo.Constraint(model.JOBS, rule=cmax_rule)

    model.obj = pyo.Objective(expr=model.Cmax, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}