import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    durations = params["durations"]
    n = len(durations)
    edges = [(0, 1), (2, 4), (2, 7), (3, 7), (1, 4), (2, 3), (0, 5), (2, 5), (3, 5)]

    horizon = sum(durations)

    model = pyo.ConcreteModel()
    model.devices = pyo.RangeSet(0, n - 1)
    model.times = pyo.RangeSet(0, horizon)

    model.start = pyo.Var(model.devices, domain=pyo.NonNegativeIntegers, bounds=(0, horizon))
    model.makespan = pyo.Var(domain=pyo.NonNegativeReals, bounds=(0, horizon))

    def finish_rule(model, i):
        return model.start[i] + durations[i] <= model.makespan

    model.finish_con = pyo.Constraint(model.devices, rule=finish_rule)

    def precedence_rule(model, i, j):
        return model.start[i] + durations[i] <= model.start[j] + horizon * model.prec[(i, j)]

    # disjunctive (big-M) formulation for non-overlap
    pair_list = []
    for (i, j) in edges:
        pair_list.append((i, j))

    model.pairs = pyo.Set(initialize=pair_list, dimen=2)
    model.prec = pyo.Var(model.pairs, domain=pyo.Binary)

    def nonoverlap_rule(model, i, j):
        return model.start[i] + durations[i] <= model.start[j] + horizon * (1 - model.prec[(i, j)])

    model.nonoverlap = pyo.Constraint(model.pairs, rule=nonoverlap_rule)

    model.obj = pyo.Objective(expr=model.makespan, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}