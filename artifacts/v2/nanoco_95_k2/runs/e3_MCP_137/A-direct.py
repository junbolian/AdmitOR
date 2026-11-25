import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    durations = params["durations"]
    n = len(durations)
    edges = [(0, 1), (2, 4), (2, 7), (3, 7), (1, 4), (2, 3), (0, 5), (2, 5), (3, 5)]

    horizon = sum(durations)

    model = pyo.ConcreteModel()

    model.devices = pyo.RangeSet(0, n - 1)
    model.edge_set = pyo.Set(initialize=edges, dimen=2)

    model.start = pyo.Var(model.devices, bounds=(0, horizon), within=pyo.NonNegativeReals)
    model.makespan = pyo.Var(bounds=(0, horizon), within=pyo.NonNegativeReals)
    model.z = pyo.Var(model.edge_set, domain=pyo.Binary)

    def makespan_rule(m, i):
        return m.start[i] + durations[i] <= m.makespan

    model.makespan_con = pyo.Constraint(model.devices, rule=makespan_rule)

    bigM = horizon

    def disj_fwd_rule(m, i, j):
        return m.start[i] + durations[i] <= m.start[j] + bigM * (1 - m.z[(i, j)])

    def disj_rev_rule(m, i, j):
        return m.start[j] + durations[j] <= m.start[i] + bigM * m.z[(i, j)]

    model.disj_fwd = pyo.Constraint(model.edge_set, rule=disj_fwd_rule)
    model.disj_rev = pyo.Constraint(model.edge_set, rule=disj_rev_rule)

    model.obj = pyo.Objective(expr=model.makespan, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}