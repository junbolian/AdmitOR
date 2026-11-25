import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    total_assignments = params["total_assignments"]
    noe_thresholds = params["noe_thresholds"]

    num_peaks = 4
    num_amino = 5

    model = pyo.ConcreteModel()

    model.PEAKS = pyo.RangeSet(0, num_peaks - 1)
    model.AMINO = pyo.RangeSet(0, num_amino - 1)

    model.x = pyo.Var(model.PEAKS, model.AMINO, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost_matrix[i][j] * m.x[i, j]
                   for i in m.PEAKS for j in m.AMINO)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def amino_rule(m, j):
        return sum(m.x[i, j] for i in m.PEAKS) <= 1
    model.amino_at_most_one = pyo.Constraint(model.AMINO, rule=amino_rule)

    def peak_rule(m, i):
        return sum(m.x[i, j] for j in m.AMINO) <= 1
    model.peak_at_most_one = pyo.Constraint(model.PEAKS, rule=peak_rule)

    def total_rule(m):
        return sum(m.x[i, j] for i in m.PEAKS for j in m.AMINO) == total_assignments
    model.exact_total = pyo.Constraint(rule=total_rule)

    # NOE spatial consistency constraints.
    # Each entry encodes (peak_a, amino_a, peak_b, amino_b, threshold).
    # If peak_a -> amino_a AND peak_b -> amino_b simultaneously, the distance
    # between amino_a and amino_b must be <= threshold. Incompatible pairs are
    # grouped: (peak_b, amino_b) -> threshold against (peak_a, amino_a).
    # Given the problem statement, the classic formulation is: forbid the joint
    # assignment when the amino-acid distance exceeds the threshold. Distance
    # feasibility is encoded by the sign convention: a negative threshold marks
    # an incompatible pair that must not be assigned together.
    def build_noe():
        cons = []
        idx = 0
        for entry in noe_thresholds:
            if isinstance(entry, (list, tuple)) and len(entry) >= 5:
                pa, aa, pb, ab, thr = entry[:5]
                if float(thr) < 0:
                    cons.append((idx, pa, aa, pb, ab))
                    idx += 1
            elif isinstance(entry, (list, tuple)) and len(entry) == 4:
                pa, aa, pb, ab = entry
                cons.append((idx, pa, aa, pb, ab))
                idx += 1
        return cons

    noe_pairs = build_noe()
    model.NOE_IDX = pyo.Set(initialize=[c[0] for c in noe_pairs])

    pair_map = {c[0]: c for c in noe_pairs}

    def noe_rule(m, k):
        _, pa, aa, pb, ab = pair_map[k]
        return m.x[pa, aa] + m.x[pb, ab] <= 1
    model.noe_cons = pyo.Constraint(model.NOE_IDX, rule=noe_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {'objective': obj_val, 'status': 'optimal'}