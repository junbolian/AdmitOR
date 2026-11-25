import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    exactly_assignments = params["exactly_assignments"]
    noe_forbidden_pairs_count = params["noe_forbidden_pairs_count"]

    n_peaks = len(cost)
    n_amino = len(cost[0])

    # NOE forbidden assignment pairs: (peak_a, amino_a, peak_b, amino_b)
    # Represents that if (peak_a, amino_a) is assigned, then (peak_b, amino_b) cannot be.
    forbidden_pairs = [
        (0, 0, 3, 3),
        (0, 0, 3, 4),
        (0, 1, 3, 3),
        (0, 1, 3, 4),
        (0, 2, 3, 3),
        (0, 2, 3, 4),
        (0, 3, 3, 3),
        (0, 3, 3, 4),
        (0, 4, 3, 3),
        (0, 4, 3, 4),
        (1, 0, 2, 3),
        (1, 0, 2, 4),
        (1, 1, 2, 3),
        (1, 1, 2, 4),
        (1, 2, 2, 3),
        (1, 2, 2, 4),
        (1, 3, 2, 3),
        (1, 3, 2, 4),
        (1, 4, 2, 3),
        (1, 4, 2, 4),
        (2, 0, 1, 0),
        (2, 1, 1, 1),
        (3, 0, 0, 2),
        (3, 4, 0, 4),
    ]

    model = pyo.ConcreteModel()

    model.PEAKS = pyo.RangeSet(0, n_peaks - 1)
    model.AMINO = pyo.RangeSet(0, n_amino - 1)

    model.x = pyo.Var(model.PEAKS, model.AMINO, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.PEAKS for j in m.AMINO)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def peak_rule(m, i):
        return sum(m.x[i, j] for j in m.AMINO) <= 1

    model.peak_con = pyo.Constraint(model.PEAKS, rule=peak_rule)

    def amino_rule(m, j):
        return sum(m.x[i, j] for i in m.PEAKS) <= 1

    model.amino_con = pyo.Constraint(model.AMINO, rule=amino_rule)

    def total_rule(m):
        return sum(m.x[i, j] for i in m.PEAKS for j in m.AMINO) == exactly_assignments

    model.total_con = pyo.Constraint(rule=total_rule)

    def noe_rule(m, k):
        a_peak, a_amino, b_peak, b_amino = forbidden_pairs[k]
        return m.x[a_peak, a_amino] + m.x[b_peak, b_amino] <= 1

    model.noe_con = pyo.Constraint(range(noe_forbidden_pairs_count), rule=noe_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}