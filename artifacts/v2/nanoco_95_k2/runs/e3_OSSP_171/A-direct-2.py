import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    jobs = ["J0", "J1", "J2"]
    machines = ["M0", "M1", "M2"]

    p = {}
    for j in jobs:
        for mach in machines:
            p[(j, mach)] = float(params["p_%s_%s" % (j, mach)])

    model = pyo.ConcreteModel()
    model.J = pyo.Set(initialize=jobs)
    model.M = pyo.Set(initialize=machines)

    # Total processing time upper bound for makespan
    bigM_val = sum(p[(j, mach)] for j in jobs for mach in machines)

    # Start time of operation (j, mach)
    model.start = pyo.Var(model.J, model.M, domain=pyo.NonNegativeReals)

    # Makespan
    model.C = pyo.Var(domain=pyo.NonNegativeReals)

    # Binary: x[j,m1,m2] = 1 if m1 precedes m2 for job j (m1 != m2)
    M_pairs = [(a, b) for a in machines for b in machines if a != b]
    model.M_pairs = pyo.Set(initialize=M_pairs, dimen=2)
    model.x = pyo.Var(model.J, model.M_pairs, domain=pyo.Binary)

    # Binary: y[a,j1,j2] = 1 if j1 precedes j2 on machine a (j1 != j2)
    J_pairs = [(a, b) for a in jobs for b in jobs if a != b]
    model.J_pairs = pyo.Set(initialize=J_pairs, dimen=2)
    model.y = pyo.Var(model.M, model.J_pairs, domain=pyo.Binary)

    # Makespan >= completion of each operation
    def makespan_rule(model, j, mach):
        return model.C >= model.start[j, mach] + p[(j, mach)]

    model.makespan_con = pyo.Constraint(model.J, model.M, rule=makespan_rule)

    # Job precedence: for each job and each pair of machines, one precedes the other
    def job_disc_rule(model, j, a, b):
        return (model.start[j, b] >= model.start[j, a] + p[(j, a)]
                - bigM_val * (1 - model.x[j, a, b]))

    model.job_disc = pyo.Constraint(
        model.J, model.M_pairs, rule=job_disc_rule)

    # Machine precedence: for each machine and each pair of jobs, one precedes the other
    def mach_disc_rule(model, mach, j1, j2):
        return (model.start[j2, mach] >= model.start[j1, mach] + p[(j1, mach)]
                - bigM_val * (1 - model.y[mach, j1, j2]))

    model.mach_disc = pyo.Constraint(
        model.M, model.J_pairs, rule=mach_disc_rule)

    # Objective
    model.obj = pyo.Objective(expr=model.C, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}