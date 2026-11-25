import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    earliest = params["earliest"]
    latest = params["latest"]
    target = params["target"]
    early_penalty = params["early_penalty"]
    late_penalty = params["late_penalty"]
    separation = params["separation"]

    n = len(earliest)
    aircraft = range(n)
    pairs = [(i, j) for i in aircraft for j in aircraft if i < j]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(aircraft)
    model.alpha = pyo.Var(aircraft, within=pyo.NonNegativeReals)
    model.beta = pyo.Var(aircraft, within=pyo.NonNegativeReals)
    model.y = pyo.Var(pairs, within=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(early_penalty[i] * model.alpha[i] + late_penalty[i] * model.beta[i]
                 for i in aircraft),
        sense=pyo.minimize,
    )

    model.window = pyo.Constraint(
        aircraft, rule=lambda m, i: pyo.inequality(earliest[i], m.x[i], latest[i])
    )

    model.early_def = pyo.Constraint(
        aircraft, rule=lambda m, i: m.alpha[i] >= target[i] - m.x[i]
    )
    model.late_def = pyo.Constraint(
        aircraft, rule=lambda m, i: m.beta[i] >= m.x[i] - target[i]
    )

    max_sep = max(separation[k] for k in separation)
    big_m = (max(latest) - min(earliest)) + max_sep

    def sep_rule(m, i, j):
        sep_ij = separation[(i, j)]
        sep_ji = separation[(j, i)]
        return (
            m.x[j] >= m.x[i] + sep_ij - big_m * (1 - m.y[(i, j)]),
            m.x[i] >= m.x[j] + sep_ji - big_m * m.y[(i, j)],
        )

    model.sep = pyo.Constraint(pairs, rule=sep_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}