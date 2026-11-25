import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    N = 5
    aircraft = list(range(N))

    earliest = {i: params[f"earliest_{i}"] for i in aircraft}
    latest = {i: params[f"latest_{i}"] for i in aircraft}
    target = {i: params[f"target_{i}"] for i in aircraft}
    early_cost = {i: params[f"early_cost_{i}"] for i in aircraft}
    late_cost = {i: params[f"late_cost_{i}"] for i in aircraft}

    pairs = [(i, j) for i in aircraft for j in aircraft if i < j]
    sep = {(i, j): params[f"sep_{i}_{j}"] for (i, j) in pairs}

    model = pyo.ConcreteModel()

    model.A = pyo.Set(initialize=aircraft)
    model.P = pyo.Set(initialize=pairs, dimen=2)

    model.t = pyo.Var(model.A, within=pyo.Reals)
    model.e = pyo.Var(model.A, within=pyo.NonNegativeReals)
    model.l = pyo.Var(model.A, within=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, within=pyo.Binary)

    model.cost = pyo.Objective(
        expr=sum(early_cost[i] * model.e[i] + late_cost[i] * model.l[i] for i in model.A),
        sense=pyo.minimize,
    )

    def _window(m, i):
        return (earliest[i], m.t[i], latest[i])
    model.window = pyo.Constraint(model.A, rule=_window)

    def _dev(m, i):
        return m.t[i] - target[i] == m.l[i] - m.e[i]
    model.dev = pyo.Constraint(model.A, rule=_dev)

    M = 1000
    def _sep_ij(m, i, j):
        return m.t[j] - m.t[i] >= sep[(i, j)] - M * (1 - m.y[i, j])
    model.sep_ij = pyo.Constraint(model.P, rule=_sep_ij)

    def _sep_ji(m, i, j):
        return m.t[i] - m.t[j] >= sep[(i, j)] - M * m.y[i, j]
    model.sep_ji = pyo.Constraint(model.P, rule=_sep_ji)

    Highs().solve(model)

    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}