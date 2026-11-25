import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    processing_times = params["processing_times"]

    routes = {
        0: [2, 0, 1],
        1: [0, 2, 1],
        2: [0, 2, 1],
    }
    num_batches = 3

    total_time = 0
    for j in range(num_batches):
        for k in range(len(routes[j])):
            total_time += processing_times[j][k]
    M = total_time

    model = pyo.ConcreteModel()

    op_list = []
    for j in range(num_batches):
        for k in range(len(routes[j])):
            op_list.append((j, k))
    model.OPS = pyo.Set(initialize=op_list, dimen=2)

    # Start times of each operation
    model.S = pyo.Var(model.OPS, domain=pyo.NonNegativeReals, bounds=(0, total_time))

    # Makespan
    model.makespan = pyo.Var(domain=pyo.NonNegativeReals, bounds=(0, total_time))

    # Precedence within each batch
    def precedence_rule(m, j, k):
        if k == 0:
            return pyo.Constraint.Skip
        return m.S[j, k] >= m.S[j, k - 1] + processing_times[j][k - 1]
    model.precedence = pyo.Constraint(model.OPS, rule=precedence_rule)

    # Group operations by machine
    ops_by_machine = {0: [], 1: [], 2: []}
    for j in range(num_batches):
        for k in range(len(routes[j])):
            ops_by_machine[routes[j][k]].append((j, k))

    disjunctive_pairs = []
    for mach in range(3):
        ops = ops_by_machine[mach]
        for a in range(len(ops)):
            for b in range(a + 1, len(ops)):
                disjunctive_pairs.append((ops[a], ops[b]))

    model.PAIRS = pyo.Set(initialize=range(len(disjunctive_pairs)), dimen=1)
    model.y = pyo.Var(model.PAIRS, domain=pyo.Binary)

    def disjunctive_rule(m, p):
        (j1, k1), (j2, k2) = disjunctive_pairs[p]
        p1 = processing_times[j1][k1]
        p2 = processing_times[j2][k2]
        # y=1 -> op1 finishes before op2 starts
        c1 = m.S[j1, k1] + p1 <= m.S[j2, k2] + M * (1 - m.y[p])
        # y=0 -> op2 finishes before op1 starts
        c2 = m.S[j2, k2] + p2 <= m.S[j1, k1] + M * m.y[p]
        return (c1, c2)
    model.disjunctive = pyo.Constraint(model.PAIRS, rule=disjunctive_rule)

    # Makespan >= finish of every operation
    def makespan_rule(m, j, k):
        return m.makespan >= m.S[j, k] + processing_times[j][k]
    model.makespan_con = pyo.Constraint(model.OPS, rule=makespan_rule)

    model.obj = pyo.Objective(expr=model.makespan, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}