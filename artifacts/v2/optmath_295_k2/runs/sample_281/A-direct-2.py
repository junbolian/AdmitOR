import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = params["assignment_costs"]
    total_required = params["total_assignments_required"]

    n_peaks = len(costs)
    n_amino = len(costs[0])

    peaks = list(range(n_peaks))
    aminos = list(range(n_amino))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(peaks, aminos, domain=pyo.Binary)

    def obj_rule(m):
        return sum(costs[p][a] * m.x[p, a] for p in peaks for a in aminos)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each peak assigned to at most one amino acid
    def peak_rule(m, p):
        return sum(m.x[p, a] for a in aminos) <= 1

    model.peak_con = pyo.Constraint(peaks, rule=peak_rule)

    # Each amino acid assigned to at most one peak
    def amino_rule(m, a):
        return sum(m.x[p, a] for p in peaks) <= 1

    model.amino_con = pyo.Constraint(aminos, rule=amino_rule)

    # Exactly total_required assignments
    def total_rule(m):
        return sum(m.x[p, a] for p in peaks for a in aminos) == total_required

    model.total_con = pyo.Constraint(rule=total_rule)

    # NOE constraints: if Peak p assigned to Amino a, then Peak q cannot be
    # assigned to Amino b for b in restricted list.
    # From the problem description:
    #   Peak 0 -> Amino 0  forbids Peak 4 -> Amino 1, 3, 4
    #   Peak 1 -> Amino 0  forbids Peak 2 -> Amino 1, 3, 4
    noe_pairs = [
        (0, 0, 4, 1),
        (0, 0, 4, 3),
        (0, 0, 4, 4),
        (1, 0, 2, 1),
        (1, 0, 2, 3),
        (1, 0, 2, 4),
    ]

    def noe_rule(m, k):
        p, a, q, b = noe_pairs[k]
        if p in peaks and q in peaks and a in aminos and b in aminos:
            return m.x[p, a] + m.x[q, b] <= 1
        return pyo.Constraint.Skip

    model.noe_con = pyo.Constraint(range(len(noe_pairs)), rule=noe_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}