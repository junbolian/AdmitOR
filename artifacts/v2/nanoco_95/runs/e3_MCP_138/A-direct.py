import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    durations = params["durations"]
    conflicts = params["conflicts"]

    n = len(durations)

    # Big-M: total sum of durations bounds any makespan
    total_dur = sum(durations.values()) if isinstance(durations, dict) else sum(durations)

    model = pyo.ConcreteModel()

    # Sets
    model.F = pyo.RangeSet(0, n - 1)

    def conflict_init(m):
        return [tuple(c) for c in conflicts]

    model.C = pyo.Set(initialize=conflict_init, dimen=2)

    # Start times (continuous, non-negative)
    model.start = pyo.Var(model.F, domain=pyo.NonNegativeReals)

    # Makespan
    model.makespan = pyo.Var(domain=pyo.NonNegativeReals)

    # Binary ordering variables for each conflict pair
    model.y = pyo.Var(model.C, domain=pyo.Binary)

    # Objective: minimize makespan
    model.total_span = pyo.Objective(expr=model.makespan, sense=pyo.minimize)

    # Makespan >= finish time of each flight
    def makespan_rule(m, i):
        return m.makespan >= m.start[i] + durations[i]

    model.makespan_con = pyo.Constraint(model.F, rule=makespan_rule)

    # Conflict constraints: for pair (i, j), either
    #   start[i] + dur[i] <= start[j]   (y=0)
    #   start[j] + dur[j] <= start[i]   (y=1)
    def conflict_rule(m, i, j):
        return m.start[i] + durations[i] <= m.start[j] + total_dur * m.y[i, j]

    def conflict_rule2(m, i, j):
        return m.start[j] + durations[j] <= m.start[i] + total_dur * (1 - m.y[i, j])

    model.conflict_a = pyo.Constraint(model.C, rule=conflict_rule)
    model.conflict_b = pyo.Constraint(model.C, rule=conflict_rule2)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_span))
    return {"objective": obj_val, "status": "optimal"}