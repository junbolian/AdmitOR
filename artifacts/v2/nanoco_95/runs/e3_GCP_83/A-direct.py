import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = params["num_variables"]
    pairs = params["interference_pairs"]

    max_colors = n

    model = pyo.ConcreteModel()
    model.V = pyo.RangeSet(0, n - 1)
    model.C = pyo.RangeSet(0, max_colors - 1)

    model.x = pyo.Var(model.V, model.C, domain=pyo.Binary)
    model.y = pyo.Var(model.C, domain=pyo.Binary)

    model.assign_con = pyo.Constraint(
        model.V,
        rule=lambda m, v: sum(m.x[v, c] for c in m.C) == 1,
    )

    def _interf(m, v, w, c):
        return m.x[v, c] + m.x[w, c] <= 1

    model.interf_con = pyo.Constraint(
        [(v, w, c) for (v, w) in pairs for c in range(max_colors)],
        rule=_interf,
    )

    def _use(m, v, c):
        return m.x[v, c] <= m.y[c]

    model.use_con = pyo.Constraint(
        [(v, c) for v in range(n) for c in range(max_colors)],
        rule=_use,
    )

    def _obj(m):
        return sum(m.y[c] for c in m.C)

    model.obj = pyo.Objective(rule=_obj, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}