import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    pt = params["processing_time"]
    big_M = params["big_M"]

    # Each job has 2 operations: (job, op)
    jobs = [0, 1, 2]
    ops = [0, 1]
    all_ops = [(j, o) for j in jobs for o in ops]

    # Machine assignment (structural). Standard job-shop 3x2 layout.
    # Assign so that each operation has a machine; operations on same machine must not overlap.
    # Job0: op0 -> M0, op1 -> M1
    # Job1: op0 -> M1, op1 -> M2
    # Job2: op0 -> M2, op1 -> M0
    machine_of = {
        (0, 0): 0, (0, 1): 1,
        (1, 0): 1, (1, 1): 2,
        (2, 0): 2, (2, 1): 0,
    }

    # Pairs of operations sharing the same machine (unordered pairs)
    machine_pairs = []
    for a in range(len(all_ops)):
        for b in range(a + 1, len(all_ops)):
            op_a = all_ops[a]
            op_b = all_ops[b]
            if machine_of[op_a] == machine_of[op_b]:
                machine_pairs.append((op_a, op_b))

    model = pyo.ConcreteModel()

    model.OPS = pyo.Set(initialize=all_ops, dimen=2)
    model.PAIRS = pyo.Set(initialize=machine_pairs, dimen=4)

    model.start = pyo.Var(model.OPS, domain=pyo.NonNegativeReals)
    model.makespan = pyo.Var(domain=pyo.NonNegativeReals)
    model.pairwise = pyo.Var(model.PAIRS, domain=pyo.Binary)

    # Precedence constraints: op1 starts at least pt after op0 completes
    def precedence_rule(m, j):
        return m.start[j, 1] >= m.start[j, 0] + pt
    model.precedence = pyo.Constraint(jobs, rule=precedence_rule)

    # Machine disjunctive constraints using big-M and binary ordering variable
    def machine_rule(m, a0, a1, b0, b1):
        return m.start[a0, a1] + pt <= m.start[b0, b1] + big_M * (1 - m.pairwise[a0, a1, b0, b1])

    def machine_rule2(m, a0, a1, b0, b1):
        return m.start[b0, b1] + pt <= m.start[a0, a1] + big_M * m.pairwise[a0, a1, b0, b1]

    model.machine_a = pyo.Constraint(model.PAIRS, rule=machine_rule)
    model.machine_b = pyo.Constraint(model.PAIRS, rule=machine_rule2)

    # Makespan definition
    def makespan_rule(m, j, o):
        return m.makespan >= m.start[j, o] + pt
    model.makespan_def = pyo.Constraint(model.OPS, rule=makespan_rule)

    model.obj = pyo.Objective(expr=model.makespan, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}