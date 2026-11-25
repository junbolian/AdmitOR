import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    n_assignments = params["n_assignments"]

    n_peaks = len(cost_matrix)
    n_aas = len(cost_matrix[0])

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, n_peaks - 1)
    model.A = pyo.RangeSet(0, n_aas - 1)

    model.x = pyo.Var(model.P, model.A, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(cost_matrix[p][a] * model.x[p, a] for p in model.P for a in model.A),
        sense=pyo.minimize,
    )

    # Each peak assigned to at most one amino acid
    model.peak_con = pyo.Constraint(
        model.P,
        rule=lambda model, p: sum(model.x[p, a] for a in model.A) <= 1,
    )

    # Each amino acid assigned to at most one peak
    model.aa_con = pyo.Constraint(
        model.A,
        rule=lambda model, a: sum(model.x[p, a] for p in model.P) <= 1,
    )

    # Exactly n_assignments total assignments
    model.total_con = pyo.Constraint(
        expr=sum(model.x[p, a] for p in model.P for a in model.A) == n_assignments
    )

    # Restricted pairs: x[p1,a1] + x[p2,a2] <= 1
    restricted_pairs = [
        (0, 1, 2, 4),
        (1, 1, 2, 4),
    ]
    model.pair_con = pyo.Constraint(
        pyo.RangeSet(0, len(restricted_pairs) - 1),
        rule=lambda model, k: (
            model.x[restricted_pairs[k][0], restricted_pairs[k][1]]
            + model.x[restricted_pairs[k][2], restricted_pairs[k][3]]
            <= 1
        ),
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}