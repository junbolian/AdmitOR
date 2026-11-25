import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    n_peaks = len(cost)
    n_amino = len(cost[0])

    model = pyo.ConcreteModel()

    model.PEAKS = pyo.RangeSet(0, n_peaks - 1)
    model.AMINO = pyo.RangeSet(0, n_amino - 1)

    model.x = pyo.Var(model.PEAKS, model.AMINO, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[p][a] * m.x[p, a] for p in m.PEAKS for a in m.AMINO)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def peak_rule(m, p):
        return sum(m.x[p, a] for a in m.AMINO) <= 1

    model.peak_con = pyo.Constraint(model.PEAKS, rule=peak_rule)

    def amino_rule(m, a):
        return sum(m.x[p, a] for p in m.PEAKS) <= 1

    model.amino_con = pyo.Constraint(model.AMINO, rule=amino_rule)

    def total_rule(m):
        return sum(m.x[p, a] for p in m.PEAKS for a in m.AMINO) == 2

    model.total_con = pyo.Constraint(rule=total_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}