import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    earliest = params["earliest"]
    latest = params["latest"]
    target = params["target"]
    early_penalty = params["early_penalty"]
    late_penalty = params["late_penalty"]
    separation = params["separation"]

    n = len(earliest)
    pairs = [(i, j) for i in range(n) for j in range(n) if i != j]

    model = pyo.ConcreteModel()

    model.A = pyo.RangeSet(0, n - 1)

    model.t = pyo.Var(model.A, within=pyo.NonNegativeReals)
    model.early = pyo.Var(model.A, within=pyo.NonNegativeReals)
    model.late = pyo.Var(model.A, within=pyo.NonNegativeReals)
    model.z = pyo.Var(pairs, within=pyo.Binary)

    model.time_window = pyo.Constraint(
        model.A, rule=lambda m, i: pyo.inequality(earliest[i], m.t[i], latest[i])
    )

    model.early_def = pyo.Constraint(
        model.A, rule=lambda m, i: m.early[i] >= target[i] - m.t[i]
    )

    model.late_def = pyo.Constraint(
        model.A, rule=lambda m, i: m.late[i] >= m.t[i] - target[i]
    )

    bigM = {(i, j): latest[i] - earliest[i] + separation[(i, j)]
            for (i, j) in pairs}

    def separation_rule(m, i, j):
        return m.t[j] >= m.t[i] + separation[(i, j)] - bigM[(i, j)] * (1 - m.z[(i, j)])

    model.sep_rule = pyo.Constraint(pairs, rule=separation_rule)

    pairs_ordered = [(i, j) for i in range(n) for j in range(i + 1, n)]

    model.order_logic = pyo.Constraint(
        pairs_ordered,
        rule=lambda m, i, j: m.z[(i, j)] + m.z[(j, i)] == 1,
    )

    def obj_rule(m):
        return sum(early_penalty[i] * m.early[i] + late_penalty[i] * m.late[i]
                   for i in m.A)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}