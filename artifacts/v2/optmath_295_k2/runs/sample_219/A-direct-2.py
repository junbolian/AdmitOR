import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    total_assignments = params["total_assignments"]
    noe_thresholds = params["noe_thresholds"]

    n_peaks = len(cost_matrix)
    n_aa = len(cost_matrix[0])

    peak_idx = list(range(n_peaks))
    aa_idx = list(range(n_aa))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(peak_idx, aa_idx, domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(cost_matrix[i][j] * mdl.x[i, j] for i in peak_idx for j in aa_idx)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each amino acid assigned to at most one peak
    def aa_rule(mdl, j):
        return sum(mdl.x[i, j] for i in peak_idx) <= 1

    model.aa_constraint = pyo.Constraint(aa_idx, rule=aa_rule)

    # Each peak assigned to at most one amino acid
    def peak_rule(mdl, i):
        return sum(mdl.x[i, j] for j in aa_idx) <= 1

    model.peak_constraint = pyo.Constraint(peak_idx, rule=peak_rule)

    # Exactly total_assignments assignments
    def count_rule(mdl):
        return sum(mdl.x[i, j] for i in peak_idx for j in aa_idx) == total_assignments

    model.count_constraint = pyo.Constraint(rule=count_rule)

    # NOE constraints.
    # noe_thresholds may be a dict keyed by tuples OR a list of entries.
    # Normalize to a list of (peak_p, aa_p, peak_q, aa_q) pairs.
    noe_pairs = []

    if isinstance(noe_thresholds, dict):
        for key in noe_thresholds:
            peak_p, aa_p, peak_q, aa_q = key
            noe_pairs.append((peak_p, aa_p, peak_q, aa_q))
    else:
        for entry in noe_thresholds:
            if isinstance(entry, dict):
                peak_p = entry["peak_p"]
                aa_p = entry["aa_p"]
                peak_q = entry["peak_q"]
                aa_q = entry["aa_q"]
                noe_pairs.append((peak_p, aa_p, peak_q, aa_q))
            else:
                peak_p, aa_p, peak_q, aa_q = entry[0], entry[1], entry[2], entry[3]
                noe_pairs.append((peak_p, aa_p, peak_q, aa_q))

    # Only keep pairs that reference valid indices
    valid_pairs = []
    for (peak_p, aa_p, peak_q, aa_q) in noe_pairs:
        if (peak_p in peak_idx and aa_p in aa_idx
                and peak_q in peak_idx and aa_q in aa_idx):
            # Avoid trivial self-conflict on identical variables
            if not (peak_p == peak_q and aa_p == aa_q):
                valid_pairs.append((peak_p, aa_p, peak_q, aa_q))

    if len(valid_pairs) > 0:
        def noe_rule(mdl, k):
            peak_p, aa_p, peak_q, aa_q = valid_pairs[k]
            return mdl.x[peak_p, aa_p] + mdl.x[peak_q, aa_q] <= 1

        model.noe_set = pyo.Set(initialize=list(range(len(valid_pairs))))
        model.noe_constraint = pyo.Constraint(model.noe_set, rule=noe_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}