import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Read numeric data from params with tolerant key lookup
    def _get(d, *names):
        for nm in names:
            if nm in d:
                return d[nm]
        # case-insensitive fallback
        lower = {str(key).lower(): val for key, val in d.items()}
        for nm in names:
            if nm.lower() in lower:
                return lower[nm.lower()]
        raise KeyError(names[0])

    a = _get(params, "a")
    b = _get(params, "b")
    m = _get(params, "m")
    n = _get(params, "n")
    k = _get(params, "k")
    d = _get(params, "d")
    c = _get(params, "c")

    model = pyo.ConcreteModel()

    model.x1 = pyo.Var(bounds=(0, None))
    model.x2 = pyo.Var(bounds=(0, None))

    model.hours = pyo.Constraint(
        expr=a * model.x1 + b * model.x2 <= c
    )
    model.production = pyo.Constraint(
        expr=k * model.x1 + k * model.x2 >= d
    )

    model.cost = pyo.Objective(
        expr=m * model.x1 + n * model.x2,
        sense=pyo.minimize,
    )

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.cost))
    except Exception:
        return {"objective": None, "status": "infeasible"}

    return {"objective": obj_val, "status": "optimal"}