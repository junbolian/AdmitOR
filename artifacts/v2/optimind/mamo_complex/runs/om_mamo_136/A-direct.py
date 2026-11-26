import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    a = params["a"]
    b = params["b"]
    n = len(a)

    model = pyo.ConcreteModel()

    model.F = pyo.RangeSet(0, n - 1)
    model.P = pyo.RangeSet(0, n - 2)

    model.t = pyo.Var(model.F)
    model.s = pyo.Var()

    def land_lb(mdl, j):
        return mdl.t[j] >= a[j]

    def land_ub(mdl, j):
        return mdl.t[j] <= b[j]

    def sep(mdl, j):
        return mdl.t[j + 1] - mdl.t[j] >= mdl.s

    model.land_lb_c = pyo.Constraint(model.F, rule=land_lb)
    model.land_ub_c = pyo.Constraint(model.F, rule=land_ub)
    model.sep_c = pyo.Constraint(model.P, rule=sep)

    model.obj = pyo.Objective(expr=model.s, sense=pyo.maximize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible"}