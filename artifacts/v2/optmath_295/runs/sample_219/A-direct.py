import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = params["costs"]
    total_assignments = params["total_assignments"]

    num_peaks = len(costs)
    num_aa = len(costs[0])

    # NOE pairwise incompatibilities: (peak_i, aa_j, peak_k, aa_l)
    # If peak_i -> aa_j then peak_k cannot -> aa_l (and vice versa).
    noe_pairs = [
        (1, 1, 3, 0),
        (1, 2, 3, 0),
    ]

    model = pyo.ConcreteModel()

    model.PEAKS = pyo.RangeSet(0, num_peaks - 1)
    model.AAS = pyo.RangeSet(0, num_aa - 1)

    model.x = pyo.Var(model.PEAKS, model.AAS, domain=pyo.Binary)

    def obj_rule(m):
        return sum(costs[i][j] * m.x[i, j] for i in m.PEAKS for j in m.AAS)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each peak assigned to at most one amino acid
    def peak_rule(m, i):
        return sum(m.x[i, j] for j in m.AAS) <= 1

    model.peak_con = pyo.Constraint(model.PEAKS, rule=peak_rule)

    # Each amino acid assigned to at most one peak
    def aa_rule(m, j):
        return sum(m.x[i, j] for i in m.PEAKS) <= 1

    model.aa_con = pyo.Constraint(model.AAS, rule=aa_rule)

    # Exactly total_assignments assignments
    def total_rule(m):
        return sum(m.x[i, j] for i in m.PEAKS for j in m.AAS) == total_assignments

    model.total_con = pyo.Constraint(rule=total_rule)

    # NOE constraints (hard incompatibilities)
    model.noe_con = pyo.ConstraintList()
    for (pi, aj, pk, al) in noe_pairs:
        model.noe_con.add(model.x[pi, aj] + model.x[pk, al] <= 1)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}