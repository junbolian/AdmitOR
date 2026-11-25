import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    p = params["p"]

    num_jobs = len(p)
    num_stages = len(p[0])

    model = pyo.ConcreteModel()

    model.JOBS = pyo.RangeSet(0, num_jobs - 1)
    model.STAGES = pyo.RangeSet(0, num_stages - 1)
    model.POS = pyo.RangeSet(0, num_jobs - 1)

    # x[k, i] = 1 if job i is scheduled at position k
    model.x = pyo.Var(model.POS, model.JOBS, domain=pyo.Binary)

    # C[k, s] = completion time of the job at position k on stage s
    model.C = pyo.Var(model.POS, model.STAGES, domain=pyo.NonNegativeReals)

    # Makespan
    model.makespan = pyo.Var(domain=pyo.NonNegativeReals)

    # Each position holds exactly one job
    def pos_rule(m, k):
        return sum(m.x[k, i] for i in m.JOBS) == 1

    model.pos_con = pyo.Constraint(model.POS, rule=pos_rule)

    # Each job assigned to exactly one position
    def job_rule(m, i):
        return sum(m.x[k, i] for k in m.POS) == 1

    model.job_con = pyo.Constraint(model.JOBS, rule=job_rule)

    # Stage 0 completion times
    def comp_stage0_rule(m, k):
        proc = sum(p[i][0] * m.x[k, i] for i in m.JOBS)
        if k == 0:
            return m.C[k, 0] >= proc
        return m.C[k, 0] >= m.C[k - 1, 0] + proc

    model.comp_stage0 = pyo.Constraint(model.POS, rule=comp_stage0_rule)

    # Stages s >= 1 completion times
    def comp_stage_rule(m, k, s):
        proc = sum(p[i][s] * m.x[k, i] for i in m.JOBS)
        if k == 0:
            return m.C[k, s] >= m.C[k, s - 1] + proc
        return m.C[k, s] >= m.C[k, s - 1] + proc

    model.comp_stage = pyo.Constraint(
        model.POS, model.STAGES, rule=comp_stage_rule
    )

    # Machine-precedence for stages s >= 1 and positions k >= 1
    def comp_machine_rule(m, k, s):
        if k == 0:
            return pyo.Constraint.Skip
        proc = sum(p[i][s] * m.x[k, i] for i in m.JOBS)
        return m.C[k, s] >= m.C[k - 1, s] + proc

    model.comp_machine = pyo.Constraint(
        model.POS, model.STAGES, rule=comp_machine_rule
    )

    # Makespan >= last position's last stage completion
    def makespan_rule(m):
        return m.makespan >= m.C[num_jobs - 1, num_stages - 1]

    model.makespan_con = pyo.Constraint(rule=makespan_rule)

    model.obj = pyo.Objective(expr=model.makespan, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}