def solve(params):
    import pyomo.environ as pyo
    from pyomo.contrib.appsi.solvers.highs import Highs

    p = params["p"]
    n_jobs = len(p)
    n_machines = len(p[0])

    JOBS_IDX = list(range(n_jobs))
    MACH_IDX = list(range(n_machines))
    POS_IDX = list(range(n_jobs))

    model = pyo.ConcreteModel()
    model.JOBS = pyo.Set(initialize=JOBS_IDX)
    model.MACHINES = pyo.Set(initialize=MACH_IDX)
    model.POS = pyo.Set(initialize=POS_IDX)

    model.assign = pyo.Var(model.JOBS, model.POS, domain=pyo.Binary)
    model.start = pyo.Var(model.POS, model.MACHINES, domain=pyo.NonNegativeReals)
    model.Cmax = pyo.Var(domain=pyo.NonNegativeReals)

    # processing time of whichever job sits at position k on machine m
    def pt(k, m):
        return sum(p[j][m] * model.assign[j, k] for j in JOBS_IDX)

    def one_pos_per_job_rule(mdl, j):
        return sum(mdl.assign[j, k] for k in POS_IDX) == 1

    def one_job_per_pos_rule(mdl, k):
        return sum(mdl.assign[j, k] for j in JOBS_IDX) == 1

    model.one_pos_per_job = pyo.Constraint(model.JOBS, rule=one_pos_per_job_rule)
    model.one_job_per_pos = pyo.Constraint(model.POS, rule=one_job_per_pos_rule)

    model.start_origin = pyo.Constraint(expr=model.start[0, 0] == 0)

    # job flow: same job must finish machine m-1 before starting machine m
    def job_flow_rule(mdl, k, m):
        if m == 0:
            return pyo.Constraint.Skip
        return mdl.start[k, m] >= mdl.start[k, m - 1] + pt(k, m - 1)

    # machine sequencing: position k starts after position k-1 finishes on same machine
    def machine_seq_rule(mdl, k, m):
        if k == 0:
            return pyo.Constraint.Skip
        return mdl.start[k, m] >= mdl.start[k - 1, m] + pt(k - 1, m)

    model.job_flow = pyo.Constraint(model.POS, model.MACHINES, rule=job_flow_rule)
    model.machine_seq = pyo.Constraint(model.POS, model.MACHINES, rule=machine_seq_rule)

    def makespan_rule(mdl, k):
        return mdl.Cmax >= mdl.start[k, n_machines - 1] + pt(k, n_machines - 1)

    model.makespan = pyo.Constraint(model.POS, rule=makespan_rule)

    model.objective = pyo.Objective(expr=model.Cmax, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.objective))
    return {"objective": obj_val, "status": "optimal"}