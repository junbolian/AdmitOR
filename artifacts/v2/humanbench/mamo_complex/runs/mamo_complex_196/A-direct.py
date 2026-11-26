import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = int(params["n"])
    a = [params["a"][i] for i in range(n)]
    b = [params["b"][i] for i in range(n)]

    model = pyo.ConcreteModel()
    model.F = pyo.RangeSet(0, n - 1)

    model.t = pyo.Var(model.F)
    model.s = pyo.Var(within=pyo.NonNegativeReals)

    model.obj = pyo.Objective(expr=model.s, sense=pyo.maximize)

    model.bounds = pyo.ConstraintList()
    for i in range(n):
        model.bounds.add(model.t[i] >= a[i])
        model.bounds.add(model.t[i] <= b[i])

    model.sep = pyo.ConstraintList()
    for i in range(n - 1):
        model.sep.add(model.t[i + 1] - model.t[i] >= model.s)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}