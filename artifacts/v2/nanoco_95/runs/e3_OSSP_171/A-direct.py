import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    jobs = ["J0", "J1", "J2"]
    machines = ["M0", "M1", "M2"]

    pt = {}
    for job in jobs:
        for mach in machines:
            pt[(job, mach)] = params["processing_time_%s_%s" % (job, mach)]

    M_big = sum(pt.values())

    model = pyo.ConcreteModel()

    model.JOBS = pyo.Set(initialize=jobs)
    model.MACHS = pyo.Set(initialize=machines)
    model.TASKS = pyo.Set(initialize=[(j, m) for j in jobs for m in machines],
                         dimen=2)

    # Operation start times
    model.start = pyo.Var(model.TASKS, within=pyo.NonNegativeReals)

    # Binary disjunction variables defined BEFORE any constraint that uses them
    # y[m, j1, j2] = 1 means j1 is processed before j2 on machine m
    model.y = pyo.Var(model.MACHS, model.JOBS, model.JOBS, within=pyo.Binary)
    # z[j, m1, m2] = 1 means machine m1 is used before m2 for job j
    model.z = pyo.Var(model.JOBS, model.MACHS, model.MACHS, within=pyo.Binary)

    # Makespan variable
    model.makespan = pyo.Var(within=pyo.NonNegativeReals)

    model.op_obj = pyo.Objective(expr=model.makespan, sense=pyo.minimize)

    # No overlap on the same machine
    def machine_disj_rule(m, m_, j1, j2):
        if j1 == j2:
            return pyo.Constraint.Skip
        return model.start[(j1, m_)] + pt[(j1, m_)] <= model.start[(j2, m_)] \
            + M_big * (1 - model.y[(m_, j1, j2)])
    model.machine_disj = pyo.Constraint(
        model.MACHS, model.JOBS, model.JOBS, rule=machine_disj_rule)

    # Ordering consistency on each machine
    def pair_order_rule(m, m_, j1, j2):
        if j1 < j2:
            return model.y[(m_, j1, j2)] + model.y[(m_, j2, j1)] == 1
        return pyo.Constraint.Skip
    model.pair_order = pyo.Constraint(
        model.MACHS, model.JOBS, model.JOBS, rule=pair_order_rule)

    # No overlap on the same job (across machines)
    def job_disj_rule(m, j_, m1, m2):
        if m1 == m2:
            return pyo.Constraint.Skip
        return model.start[(j_, m1)] + pt[(j_, m1)] <= model.start[(j_, m2)] \
            + M_big * (1 - model.z[(j_, m1, m2)])
    model.job_disj = pyo.Constraint(
        model.JOBS, model.MACHS, model.MACHS, rule=job_disj_rule)

    def job_order_rule(m, j_, m1, m2):
        if m1 < m2:
            return model.z[(j_, m1, m2)] + model.z[(j_, m2, m1)] == 1
        return pyo.Constraint.Skip
    model.job_order = pyo.Constraint(
        model.JOBS, model.MACHS, model.MACHS, rule=job_order_rule)

    # Makespan definition
    def makespan_rule(m, j_, m_):
        return model.makespan >= model.start[(j_, m_)] + pt[(j_, m_)]
    model.makespan_def = pyo.Constraint(
        model.JOBS, model.MACHS, rule=makespan_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.op_obj))
    return {"objective": obj_val, "status": "optimal"}