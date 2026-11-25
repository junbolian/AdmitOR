import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    aircraft = list(range(4))
    pairs = [(i, j) for i in aircraft for j in aircraft if i != j]

    early_penalty = params["early_penalty"]
    late_penalty = params["late_penalty"]
    earliest_landing = params["earliest_landing"]
    latest_landing = params["latest_landing"]
    target_landing = params["target_landing"]

    sep_raw = params["separation_i_before_j"]

    def sep_val(i, j):
        try:
            return sep_raw[i][j]
        except (KeyError, IndexError, TypeError):
            pass
        try:
            return sep_raw[(i, j)]
        except (KeyError, IndexError, TypeError):
            pass
        try:
            return sep_raw[str(i)][str(j)]
        except (KeyError, IndexError, TypeError):
            pass
        try:
            return sep_raw["%d_%d" % (i, j)]
        except (KeyError, IndexError, TypeError):
            pass
        try:
            return sep_raw["%d,%d" % (i, j)]
        except (KeyError, IndexError, TypeError):
            pass
        return sep_raw[i * 4 + j]

    model = pyo.ConcreteModel()

    model.A = pyo.Set(initialize=aircraft)
    model.P = pyo.Set(initialize=pairs, dimen=2)

    model.t = pyo.Var(model.A)
    model.early = pyo.Var(model.A, domain=pyo.NonNegativeReals)
    model.late = pyo.Var(model.A, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, domain=pyo.Binary)

    model.order = pyo.Constraint(
        model.P, rule=lambda m, i, j: m.y[i, j] + m.y[j, i] == 1 if i < j else pyo.Constraint.Skip
    )

    model.tw_lo = pyo.Constraint(model.A, rule=lambda m, i: m.t[i] >= earliest_landing[i])
    model.tw_hi = pyo.Constraint(model.A, rule=lambda m, i: m.t[i] <= latest_landing[i])

    model.dev = pyo.Constraint(
        model.A, rule=lambda m, i: m.t[i] - target_landing[i] == m.late[i] - m.early[i]
    )

    big_m = (max(latest_landing[i] for i in aircraft)
             - min(earliest_landing[i] for i in aircraft)
             + max(sep_val(i, j) for (i, j) in pairs))

    model.sep = pyo.Constraint(
        model.P,
        rule=lambda m, i, j: m.t[j] >= m.t[i] + sep_val(i, j) - big_m * (1 - m.y[i, j]),
    )

    model.total_penalty = pyo.Objective(
        expr=sum(
            early_penalty[i] * model.early[i] + late_penalty[i] * model.late[i]
            for i in model.A
        ),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_penalty))
    return {"objective": obj_val, "status": "optimal"}