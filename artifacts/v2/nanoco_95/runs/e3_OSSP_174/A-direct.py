import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    jobs = ["J0", "J1", "J2"]
    machines = ["M0", "M1", "M2"]

    dur = {}
    for j in jobs:
        for m in machines:
            dur[(j, m)] = params["duration_" + j + "_" + m]

    bigM = sum(dur.values())

    model = pyo.ConcreteModel()

    model.JOBS = pyo.Set(initialize=jobs)
    model.MACHINES = pyo.Set(initialize=machines)
    model.TASKS = pyo.Set(
        initialize=[(j, m) for j in jobs for m in machines], dimen=2
    )

    model.start = pyo.Var(model.TASKS, domain=pyo.NonNegativeReals)
    model.makespan_var = pyo.Var(domain=pyo.NonNegativeReals)

    pair_list = [
        (i, k)
        for i in model.TASKS
        for k in model.TASKS
        if i[1] == k[1] and i[0] != k[0]
    ]
    model.machine_pair = pyo.Set(initialize=pair_list, dimen=2)
    model.z = pyo.Var(model.machine_pair, domain=pyo.Binary)

    def machine_prec_rule(model, i, k):
        return model.start[k] >= model.start[i] + dur[i] - bigM * (
            1 - model.z[i, k]
        )

    model.machine_prec = pyo.Constraint(model.machine_pair, rule=machine_prec_rule)

    job_pair_list = [
        (i, k)
        for i in model.TASKS
        for k in model.TASKS
        if i[0] == k[0] and i[1] != k[1]
    ]
    model.job_pair = pyo.Set(initialize=job_pair_list, dimen=2)
    model.y = pyo.Var(model.job_pair, domain=pyo.Binary)

    def job_prec_rule(model, i, k):
        return model.start[k] >= model.start[i] + dur[i] - bigM * (
            1 - model.y[i, k]
        )

    model.job_prec = pyo.Constraint(model.job_pair, rule=job_prec_rule)

    def makespan_rule(model, j, m):
        return model.makespan_var >= model.start[j, m] + dur[(j, m)]

    model.makespan_con = pyo.Constraint(model.TASKS, rule=makespan_rule)

    model.obj = pyo.Objective(expr=model.makespan_var, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}