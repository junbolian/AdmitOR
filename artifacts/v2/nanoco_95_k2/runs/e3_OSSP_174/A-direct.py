import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    pt = params["processing_time"]
    jobs = [0, 1, 2]
    machines = [0, 1, 2]

    def dur(j, k):
        # pt is a nested matrix: pt[j][k]
        return pt[j][k]

    model = pyo.ConcreteModel()

    model.J = pyo.Set(initialize=jobs)
    model.M = pyo.Set(initialize=machines)
    model.JM = pyo.Set(initialize=[(j, k) for j in jobs for k in machines])

    # Pairs of operations on the SAME job (different machines)
    model.PairsJ = pyo.Set(
        initialize=[((j, k), (j, kk))
                    for j in jobs
                    for k in machines
                    for kk in machines if k < kk]
    )

    # Pairs of operations on the SAME machine (different jobs)
    model.PairsM = pyo.Set(
        initialize=[((j, k), (jj, k))
                    for k in machines
                    for j in jobs
                    for jj in jobs if j < jj]
    )

    # Big-M
    horizon = sum(dur(j, k) for j in jobs for k in machines)
    model.big_M = pyo.Param(initialize=horizon)

    # Start time of operation (j,k)
    model.x = pyo.Var(model.JM, within=pyo.NonNegativeReals)
    # Makespan
    model.C = pyo.Var(within=pyo.NonNegativeReals)
    # Ordering binaries
    model.y_job = pyo.Var(model.PairsJ, within=pyo.Binary)
    model.y_mach = pyo.Var(model.PairsM, within=pyo.Binary)

    # Objective: minimize makespan
    model.obj = pyo.Objective(expr=model.C, sense=pyo.minimize)

    # Completion >= start + duration for all operations
    model.compl = pyo.Constraint(
        model.JM,
        rule=lambda mm, j, k: model.C >= model.x[j, k] + dur(j, k)
    )

    # Non-overlap within each job (any sequence allowed)
    def prec_job(mm, a, b):
        return (model.x[b[0], b[1]]
                >= model.x[a[0], a[1]] + dur(a[0], a[1])
                - model.big_M * (1 - model.y_job[a, b]))

    def prec_job_rev(mm, a, b):
        return (model.x[a[0], a[1]]
                >= model.x[b[0], b[1]] + dur(b[0], b[1])
                - model.big_M * model.y_job[a, b])

    model.prec_job = pyo.Constraint(model.PairsJ, rule=prec_job)
    model.prec_job_rev = pyo.Constraint(model.PairsJ, rule=prec_job_rev)

    # Non-overlap on each machine
    def prec_mach(mm, a, b):
        return (model.x[b[0], b[1]]
                >= model.x[a[0], a[1]] + dur(a[0], a[1])
                - model.big_M * (1 - model.y_mach[a, b]))

    def prec_mach_rev(mm, a, b):
        return (model.x[a[0], a[1]]
                >= model.x[b[0], b[1]] + dur(b[0], b[1])
                - model.big_M * model.y_mach[a, b])

    model.prec_mach = pyo.Constraint(model.PairsM, rule=prec_mach)
    model.prec_mach_rev = pyo.Constraint(model.PairsM, rule=prec_mach_rev)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}