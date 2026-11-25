import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    durations = list(params["durations"])
    conflict_pairs = list(params["conflict_pairs"])

    n = len(durations)  # structural: 8 robots

    model = pyo.ConcreteModel()

    model.ROBOTS = pyo.RangeSet(0, n - 1)
    model.PAIRS = pyo.Set(initialize=[(int(a), int(b)) for (a, b) in conflict_pairs], dimen=2)

    horizon = int(sum(durations))  # a valid upper bound on makespan

    # start time of each robot's interval
    model.start = pyo.Var(model.ROBOTS, domain=pyo.NonNegativeIntegers, bounds=(0, horizon))
    # global makespan / max time index utilized
    model.makespan = pyo.Var(domain=pyo.NonNegativeReals, bounds=(0, horizon))
    # disjunctive binary: y[a,b] == 1 means a finishes before b starts
    model.before = pyo.Var(model.PAIRS, domain=pyo.Binary)

    # completion = start + duration, and completion <= makespan
    def completion_bound_rule(m, i):
        return m.start[i] + int(durations[i]) <= m.makespan

    model.completion_bound = pyo.Constraint(model.ROBOTS, rule=completion_bound_rule)

    # conflict: intervals [start_i, start_i + dur_i] must be non-overlapping via big-M
    M = horizon + 1

    def conflict_ab_rule(m, a, b):
        return m.start[a] + int(durations[a]) <= m.start[b] + M * (1 - m.before[a, b])

    def conflict_ba_rule(m, a, b):
        return m.start[b] + int(durations[b]) <= m.start[a] + M * m.before[a, b]

    model.conflict_ab = pyo.Constraint(model.PAIRS, rule=conflict_ab_rule)
    model.conflict_ba = pyo.Constraint(model.PAIRS, rule=conflict_ba_rule)

    model.obj = pyo.Objective(expr=model.makespan, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}