import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    dependencies = [
        (0, 1), (0, 2), (0, 3), (0, 5), (0, 6), (0, 7),
        (1, 7), (2, 4), (2, 6), (2, 7), (3, 6), (4, 6),
        (4, 7), (5, 7),
    ]
    turnaround = params["turnaround"]
    n_procs = 8

    model = pyo.ConcreteModel()
    model.P = pyo.RangeSet(0, n_procs - 1)
    model.D = pyo.RangeSet(0, len(dependencies) - 1)

    upper_bound = sum(turnaround[k] for k in range(len(dependencies))) + n_procs

    model.start = pyo.Var(model.P, domain=pyo.NonNegativeIntegers, bounds=(0, upper_bound))
    model.makespan = pyo.Var(domain=pyo.NonNegativeReals, bounds=(0, upper_bound))
    model.X = pyo.Var(model.D, domain=pyo.Binary)

    model.obj = pyo.Objective(expr=model.makespan, sense=pyo.minimize)

    def makespan_rule(m, i):
        return m.makespan >= m.start[i]

    model.makespan_con = pyo.Constraint(model.P, rule=makespan_rule)

    def dep_rule_a(m, k):
        u, v = dependencies[k]
        d = turnaround[k]
        M = upper_bound + d
        return m.start[u] - m.start[v] >= d - M * (1 - m.X[k])

    def dep_rule_b(m, k):
        u, v = dependencies[k]
        d = turnaround[k]
        M = upper_bound + d
        return m.start[v] - m.start[u] >= d - M * m.X[k]

    model.dep_con_a = pyo.Constraint(model.D, rule=dep_rule_a)
    model.dep_con_b = pyo.Constraint(model.D, rule=dep_rule_b)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}