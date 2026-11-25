import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    num_lots = 3
    num_stations = 3
    lots = range(num_lots)
    stations = range(num_stations)

    p = {}
    for l in lots:
        for s in stations:
            p[(l, s)] = params[f"p_{l}_{s}"]

    model = pyo.ConcreteModel()

    # Big-M upper bound on makespan
    M = sum(p[(l, s)] for l in lots for s in stations)

    # Decision variables
    model.start = pyo.Var(lots, stations, within=pyo.NonNegativeReals)
    model.end = pyo.Var(lots, stations, within=pyo.NonNegativeReals)
    model.makespan = pyo.Var(within=pyo.NonNegativeReals)

    # Sequence binary variables: y[l1, l2, s] = 1 if lot l1 precedes lot l2 on station s
    pairs = [(l1, l2) for l1 in lots for l2 in lots if l1 != l2]
    model.y = pyo.Var([(l1, l2, s) for (l1, l2) in pairs for s in stations], within=pyo.Binary)

    # Precedence within each lot across stations
    def prec_rule(m, l, s):
        if s == 0:
            return pyo.Constraint.Skip
        return m.start[l, s] >= m.end[l, s - 1]
    model.prec = pyo.Constraint(lots, stations, rule=prec_rule)

    # Processing time link
    def proc_rule(m, l, s):
        return m.end[l, s] == m.start[l, s] + p[(l, s)]
    model.proc = pyo.Constraint(lots, stations, rule=proc_rule)

    # No-overlap per station using big-M
    def no_overlap_rule(m, l1, l2, s):
        if l1 < l2:
            return m.start[l2, s] >= m.end[l1, s] - M * (1 - m.y[l1, l2, s])
        else:
            return m.start[l1, s] >= m.end[l2, s] - M * m.y[l2, l1, s]
    model.no_overlap = pyo.Constraint(pairs, stations, rule=no_overlap_rule)

    # Makespan >= completion on last station
    def makespan_rule(m, l):
        return m.makespan >= m.end[l, num_stations - 1]
    model.makespan_def = pyo.Constraint(lots, rule=makespan_rule)

    model.obj = pyo.Objective(expr=model.makespan, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}