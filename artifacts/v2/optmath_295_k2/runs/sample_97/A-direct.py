import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    earliest = params["earliest"]
    latest = params["latest"]
    target = params["target"]
    early_cost = params["early_cost"]
    late_cost = params["late_cost"]
    separation = params["separation"]

    n = len(earliest)
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]

    sep_vals = list(separation.values()) if hasattr(separation, "values") else list(separation)
    big_m = float(max(latest) - min(earliest)) + float(max(sep_vals))

    model = pyo.ConcreteModel()
    model.A = pyo.Set(initialize=range(n))
    model.P = pyo.Set(initialize=pairs, dimen=2)

    model.t = pyo.Var(model.A, within=pyo.Reals)
    model.early = pyo.Var(model.A, within=pyo.NonNegativeReals)
    model.late = pyo.Var(model.A, within=pyo.NonNegativeReals)
    model.z = pyo.Var(model.P, within=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(early_cost[i] * model.early[i] + late_cost[i] * model.late[i]
                 for i in model.A),
        sense=pyo.minimize,
    )

    model.time_window = pyo.Constraint(
        model.A,
        rule=lambda m, i: pyo.inequality(earliest[i], m.t[i], latest[i]),
    )

    model.defn = pyo.Constraint(
        model.A,
        rule=lambda m, i: m.t[i] - target[i] == m.late[i] - m.early[i],
    )

    model.sep = pyo.ConstraintList()
    for (i, j) in pairs:
        s = separation[(i, j)]
        model.sep.add(model.t[j] >= model.t[i] + s - big_m * (1 - model.z[(i, j)]))
        model.sep.add(model.t[i] >= model.t[j] + s - big_m * model.z[(i, j)])

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}