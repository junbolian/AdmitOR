import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    n_peaks = len(cost)
    n_aa = len(cost[0])

    model = pyo.ConcreteModel()
    model.P = pyo.RangeSet(0, n_peaks - 1)
    model.A = pyo.RangeSet(0, n_aa - 1)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.P for j in m.A)

    model.x = pyo.Var(model.P, model.A, domain=pyo.Binary)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def peak_rule(m, i):
        return sum(m.x[i, j] for j in m.A) <= 1

    model.peak_con = pyo.Constraint(model.P, rule=peak_rule)

    def aa_rule(m, j):
        return sum(m.x[i, j] for i in m.P) <= 1

    model.aa_con = pyo.Constraint(model.A, rule=aa_rule)

    def total_rule(m):
        return sum(m.x[i, j] for i in m.P for j in m.A) == 2

    model.total_con = pyo.Constraint(rule=total_rule)

    solver = Highs()
    solver.solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}