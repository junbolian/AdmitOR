import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    a = params["a"]
    b = params["b"]
    n = 10

    model = pyo.ConcreteModel()

    model.F = pyo.RangeSet(1, n)

    model.t = pyo.Var(model.F)

    model.s = pyo.Var()

    model.obj = pyo.Objective(expr=model.s, sense=pyo.maximize)

    def bound_lower(m, j):
        return m.t[j] >= a[j - 1]

    def bound_upper(m, j):
        return m.t[j] <= b[j - 1]

    model.cons_lower = pyo.Constraint(model.F, rule=bound_lower)
    model.cons_upper = pyo.Constraint(model.F, rule=bound_upper)

    def separation(m, j):
        return m.t[j + 1] - m.t[j] >= m.s

    model.cons_sep = pyo.Constraint(pyo.RangeSet(1, n - 1), rule=separation)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}