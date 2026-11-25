import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    duration = params["duration_matrix"]
    n = len(duration)

    model = pyo.ConcreteModel()
    model.analysts = pyo.RangeSet(0, n - 1)
    model.incidents = pyo.RangeSet(0, n - 1)

    model.x = pyo.Var(model.analysts, model.incidents, domain=pyo.Binary)
    model.z = pyo.Var(domain=pyo.NonNegativeReals)

    model.assign_analyst = pyo.Constraint(
        model.analysts,
        rule=lambda m, i: sum(m.x[i, j] for j in m.incidents) == 1,
    )
    model.assign_incident = pyo.Constraint(
        model.incidents,
        rule=lambda m, j: sum(m.x[i, j] for i in m.analysts) == 1,
    )
    model.bottleneck = pyo.Constraint(
        model.analysts,
        model.incidents,
        rule=lambda m, i, j: m.z >= duration[i][j] * m.x[i, j],
    )

    model.obj = pyo.Objective(expr=model.z, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}