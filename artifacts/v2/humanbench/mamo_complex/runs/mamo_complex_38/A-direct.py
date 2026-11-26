import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    a = params["a"]
    b = params["b"]
    n = len(a)

    model = pyo.ConcreteModel()

    model.F = pyo.RangeSet(0, n - 1)
    model.G = pyo.RangeSet(0, n - 2)

    model.t = pyo.Var(model.F, within=pyo.Reals)
    model.s = pyo.Var(within=pyo.NonNegativeReals)

    model.land_lb = pyo.Constraint(model.F, rule=lambda m, j: m.t[j] >= a[j])
    model.land_ub = pyo.Constraint(model.F, rule=lambda m, j: m.t[j] <= b[j])

    model.sep = pyo.Constraint(model.G, rule=lambda m, j: m.t[j + 1] - m.t[j] >= m.s)

    model.obj = pyo.Objective(expr=model.s, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}