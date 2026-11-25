import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    processing = params["processing_times"]

    # Job routes: list of (task, machine) with processing time
    routes = [
        [(0, 1), (0, 0), (0, 2)],
        [(1, 2), (1, 1), (1, 0)],
        [(2, 2), (2, 1), (2, 0)],
    ]
    num_jobs = 3
    num_ops = 3
    num_machines = 3

    p = {}
    for j in range(num_jobs):
        for k in range(num_ops):
            job, mach = routes[j][k]
            p[j, k] = processing[job][k]

    model = pyo.ConcreteModel()

    model.JOBS = pyo.RangeSet(0, num_jobs - 1)
    model.OPS = pyo.RangeSet(0, num_ops - 1)
    model.MACHINES = pyo.RangeSet(0, num_machines - 1)
    model.JOB_OP = pyo.Set(initialize=[(j, k) for j in range(num_jobs) for k in range(num_ops)], dimen=2)

    # Start times
    model.start = pyo.Var(model.JOB_OP, within=pyo.NonNegativeReals)
    model.makespan = pyo.Var(within=pyo.NonNegativeReals)

    # Disjunctive binaries for machine pairs
    machine_ops = {m: [] for m in range(num_machines)}
    for j in range(num_jobs):
        for k in range(num_ops):
            _, mach = routes[j][k]
            machine_ops[mach].append((j, k))

    pairs = []
    for m in range(num_machines):
        ops = machine_ops[m]
        for a in range(len(ops)):
            for b in range(a + 1, len(ops)):
                pairs.append((ops[a], ops[b]))
    model.PAIRS = pyo.Set(initialize=pairs, dimen=4)

    model.y = pyo.Var(model.PAIRS, within=pyo.Binary)
    model.M = sum(p[j, k] for j in range(num_jobs) for k in range(num_ops))

    # Precedence within each job
    def prec_rule(mdl, j, k):
        if k == 0:
            return pyo.Constraint.Skip
        return mdl.start[j, k] >= mdl.start[j, k - 1] + p[j, k - 1]
    model.prec = pyo.Constraint(model.JOBS, model.OPS, rule=prec_rule)

    # Machine disjunctive constraints
    def disj_rule(mdl, j1, k1, j2, k2):
        return mdl.start[j2, k2] >= mdl.start[j1, k1] + p[j1, k1] - mdl.M * mdl.y[j1, k1, j2, k2]
    model.disj1 = pyo.Constraint(model.PAIRS, rule=disj_rule)

    def disj2_rule(mdl, j1, k1, j2, k2):
        return mdl.start[j1, k1] >= mdl.start[j2, k2] + p[j2, k2] - mdl.M * (1 - mdl.y[j1, k1, j2, k2])
    model.disj2 = pyo.Constraint(model.PAIRS, rule=disj2_rule)

    # Makespan
    def makespan_rule(mdl, j, k):
        return mdl.makespan >= mdl.start[j, k] + p[j, k]
    model.makespan_con = pyo.Constraint(model.JOB_OP, rule=makespan_rule)

    model.obj = pyo.Objective(expr=model.makespan, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}