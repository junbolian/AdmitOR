import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    p = params["processing_time_per_operation"]
    M = params["big_M"]

    num_jobs = 3
    num_ops = 2
    ops = [(j, o) for j in range(num_jobs) for o in range(num_ops)]

    # Machine assignment: route each operation to a shared machine.
    machine_of = {(j, o): (j + o) % 2 for j in range(num_jobs) for o in range(num_ops)}

    # Job-precedence pairs: (earlier, later)
    job_prec = [((j, 0), (j, 1)) for j in range(num_jobs)]

    # Job pairs to order on the same machine
    machine_pairs = []
    for a in range(len(ops)):
        for b in range(a + 1, len(ops)):
            oa, ob = ops[a], ops[b]
            if machine_of[oa] == machine_of[ob]:
                machine_pairs.append((oa, ob))

    model = pyo.ConcreteModel()

    model.start = pyo.Var(ops, domain=pyo.NonNegativeReals)
    model.cmax = pyo.Var(domain=pyo.NonNegativeReals)
    model.y = pyo.Var(machine_pairs, domain=pyo.Binary)

    def precedence_rule(mdl, k):
        e, l = job_prec[k]
        return mdl.start[l] >= mdl.start[e] + p
    model.precedence = pyo.Constraint(range(len(job_prec)), rule=precedence_rule)

    def disj1_rule(mdl, k):
        oa, ob = machine_pairs[k]
        return mdl.start[ob] >= mdl.start[oa] + p - M * (1 - mdl.y[(oa, ob)])
    model.disj1 = pyo.Constraint(range(len(machine_pairs)), rule=disj1_rule)

    def disj2_rule(mdl, k):
        oa, ob = machine_pairs[k]
        return mdl.start[oa] >= mdl.start[ob] + p - M * mdl.y[(oa, ob)]
    model.disj2 = pyo.Constraint(range(len(machine_pairs)), rule=disj2_rule)

    def makespan_rule(mdl, k):
        op = ops[k]
        return mdl.cmax >= mdl.start[op] + p
    model.makespan = pyo.Constraint(range(len(ops)), rule=makespan_rule)

    model.obj = pyo.Objective(expr=model.cmax, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}