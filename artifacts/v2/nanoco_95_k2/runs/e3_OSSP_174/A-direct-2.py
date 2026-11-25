import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    processing_time = params["processing_time"]

    jobs = list(range(3))
    machines = list(range(3))

    # For each (job, machine) we need a task
    tasks = [(j, m) for j in jobs for m in machines]
    # Two tasks (j1, m1) and (j2, m2) conflict on a machine if m1 == m2
    # Two tasks conflict on a job if j1 == j2

    bigM = sum(processing_time[j][m] for j in jobs for m in machines)

    model = pyo.ConcreteModel()

    # Completion time of each task
    model.C = pyo.Var(tasks, domain=pyo.NonNegativeReals)
    # Makespan
    model.T = pyo.Var(domain=pyo.NonNegativeReals)

    # Disjunctive binary variables
    # On same machine: x[j1,m1,j2,m2] = 1 if task (j2,m2) precedes task (j1,m1)
    # On same job:    y[j1,m1,j2,m2] = 1 if task (j1,m2) precedes task (j1,m1)
    machine_pairs = []
    for m in machines:
        js = jobs
        for a in range(len(js)):
            for b in range(a + 1, len(js)):
                machine_pairs.append((js[a], m, js[b], m))

    job_pairs = []
    for j in jobs:
        ms = machines
        for a in range(len(ms)):
            for b in range(a + 1, len(ms)):
                job_pairs.append((j, ms[a], j, ms[b]))

    model.x = pyo.Var(machine_pairs, domain=pyo.Binary)
    model.y = pyo.Var(job_pairs, domain=pyo.Binary)

    def makespan_rule(mo, j, m):
        return mo.T >= mo.C[j, m]

    model.makespan_con = pyo.Constraint(tasks, rule=makespan_rule)

    # Machine disjunctive constraints
    def machine_rule(mo, j1, m1, j2, m2):
        return mo.C[j1, m1] >= mo.C[j2, m2] + processing_time[j1][m1] - bigM * (1 - mo.x[j1, m1, j2, m2])

    model.machine_con = pyo.Constraint(machine_pairs, rule=machine_rule)

    def machine_rule_rev(mo, j1, m1, j2, m2):
        return mo.C[j2, m2] >= mo.C[j1, m1] + processing_time[j2][m2] - bigM * mo.x[j1, m1, j2, m2]

    model.machine_con_rev = pyo.Constraint(machine_pairs, rule=machine_rule_rev)

    # Job disjunctive constraints
    def job_rule(mo, j1, m1, j2, m2):
        return mo.C[j1, m1] >= mo.C[j2, m2] + processing_time[j1][m1] - bigM * (1 - mo.y[j1, m1, j2, m2])

    model.job_con = pyo.Constraint(job_pairs, rule=job_rule)

    def job_rule_rev(mo, j1, m1, j2, m2):
        return mo.C[j2, m2] >= mo.C[j1, m1] + processing_time[j2][m2] - bigM * mo.y[j1, m1, j2, m2]

    model.job_con_rev = pyo.Constraint(job_pairs, rule=job_rule_rev)

    model.obj = pyo.Objective(expr=model.T, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}