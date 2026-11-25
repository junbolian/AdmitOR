import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    assignment_costs = params["assignment_costs"]
    total_assignments_required = params["total_assignments_required"]

    n_peaks = 5
    n_amino = 6

    model = pyo.ConcreteModel()

    model.PEAKS = pyo.RangeSet(0, n_peaks - 1)
    model.AMINO = pyo.RangeSet(0, n_amino - 1)

    model.x = pyo.Var(model.PEAKS, model.AMINO, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(
            assignment_costs[i][j] * model.x[i, j]
            for i in model.PEAKS
            for j in model.AMINO
        ),
        sense=pyo.minimize,
    )

    # Each peak assigned to at most one amino acid
    def peak_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.AMINO) <= 1

    model.peak_con = pyo.Constraint(model.PEAKS, rule=peak_rule)

    # Each amino acid assigned to at most one peak
    def amino_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.PEAKS) <= 1

    model.amino_con = pyo.Constraint(model.AMINO, rule=amino_rule)

    # Exactly total_assignments_required assignments
    model.total_con = pyo.Constraint(
        expr=sum(
            model.x[i, j] for i in model.PEAKS for j in model.AMINO
        ) == total_assignments_required
    )

    # NOE constraints
    noe_pairs = [
        (0, 0, 4, 1),
        (0, 0, 4, 3),
        (0, 0, 4, 4),
        (1, 0, 2, 1),
        (1, 0, 2, 3),
        (1, 0, 2, 4),
    ]

    def noe_rule(mdl, k):
        p1, a1, p2, a2 = noe_pairs[k]
        return mdl.x[p1, a1] + mdl.x[p2, a2] <= 1

    model.noe_con = pyo.Constraint(range(len(noe_pairs)), rule=noe_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}