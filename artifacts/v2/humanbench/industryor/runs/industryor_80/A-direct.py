import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    p = params["processing_times"]
    n_batches = len(p)
    n_vats = len(p[0])

    model = pyo.ConcreteModel()

    model.JOBS = pyo.RangeSet(0, n_batches - 1)
    model.VATS = pyo.RangeSet(0, n_vats - 1)

    model.start = pyo.Var(model.JOBS, model.VATS, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.JOBS, model.JOBS, model.VATS, domain=pyo.Binary)
    model.Cmax = pyo.Var(domain=pyo.NonNegativeReals)

    model.op = pyo.ConstraintList()
    model.nooverlap = pyo.ConstraintList()

    M = sum(max(p[i][j] for j in range(n_vats)) for i in range(n_batches))

    for i in model.JOBS:
        for j in model.VATS:
            if j < n_vats - 1:
                model.op.add(model.start[i, j + 1] >= model.start[i, j] + p[i][j])
            else:
                model.op.add(model.Cmax >= model.start[i, j] + p[i][j])

    for j in model.VATS:
        for i in model.JOBS:
            for k in model.JOBS:
                if i < k:
                    model.nooverlap.add(
                        model.start[i, j] + p[i][j] <= model.start[k, j] + M * (1 - model.y[i, k, j])
                    )
                    model.nooverlap.add(
                        model.start[k, j] + p[k][j] <= model.start[i, j] + M * model.y[i, k, j]
                    )

    model.obj = pyo.Objective(expr=model.Cmax, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}