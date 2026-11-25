import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    assignment_cost = params["assignment_cost"]
    num_assignments_required = params["num_assignments_required"]
    num_peaks = params["num_peaks"]
    num_amino_acids = params["num_amino_acids"]

    peaks = list(range(num_peaks))
    aas = list(range(num_amino_acids))

    # NOE constraints: (peak, aa) -> list of (peak', aa') that cannot both be assigned
    # 24 constraints derived from the narrative.
    noe_forbidden_pairs = [
        # If Peak 0 assigned to Amino Acid 0, Peak 3 cannot be AA3 or AA4
        ((0, 0), (3, 3)), ((0, 0), (3, 4)),
        # If Peak 0 assigned to Amino Acid 1, Peak 3 cannot be AA3 or AA4
        ((0, 1), (3, 3)), ((0, 1), (3, 4)),
        # If Peak 0 assigned to Amino Acid 2, Peak 3 cannot be AA3
        ((0, 2), (3, 3)),
        # If Peak 0 assigned to Amino Acid 3, Peak 3 cannot be AA1 or AA2
        ((0, 3), (3, 1)), ((0, 3), (3, 2)),
        # If Peak 0 assigned to Amino Acid 4, Peak 3 cannot be AA0 or AA1
        ((0, 4), (3, 0)), ((0, 4), (3, 1)),
        # If Peak 1 assigned to Amino Acid 0, Peak 2 cannot be AA2 or AA3
        ((1, 0), (2, 2)), ((1, 0), (2, 3)),
        # If Peak 1 assigned to Amino Acid 1, Peak 2 cannot be AA2
        ((1, 1), (2, 2)),
        # If Peak 1 assigned to Amino Acid 2, Peak 2 cannot be AA0 or AA4
        ((1, 2), (2, 0)), ((1, 2), (2, 4)),
        # If Peak 1 assigned to Amino Acid 3, Peak 2 cannot be AA1
        ((1, 3), (2, 1)),
        # If Peak 1 assigned to Amino Acid 4, Peak 2 cannot be AA0 or AA1
        ((1, 4), (2, 0)), ((1, 4), (2, 1)),
        # If Peak 2 assigned to Amino Acid 0, Peak 3 cannot be AA2
        ((2, 0), (3, 2)),
        # If Peak 2 assigned to Amino Acid 1, Peak 3 cannot be AA2 or AA4
        ((2, 1), (3, 2)), ((2, 1), (3, 4)),
        # If Peak 2 assigned to Amino Acid 2, Peak 3 cannot be AA0
        ((2, 2), (3, 0)),
        # If Peak 2 assigned to Amino Acid 3, Peak 3 cannot be AA1 or AA4
        ((2, 3), (3, 1)), ((2, 3), (3, 4)),
        # If Peak 2 assigned to Amino Acid 4, Peak 3 cannot be AA3
        ((2, 4), (3, 3)),
    ]

    model = pyo.ConcreteModel()

    model.PEAKS = pyo.Set(initialize=peaks)
    model.AAS = pyo.Set(initialize=aas)
    model.PAIRS = pyo.Set(
        initialize=[(p, a) for p in peaks for a in aas], dimen=2
    )

    model.x = pyo.Var(model.PAIRS, domain=pyo.Binary)

    def obj_rule(m):
        return sum(
            assignment_cost[p][a] * m.x[p, a] for p in peaks for a in aas
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each peak assigned to at most one amino acid
    def peak_rule(m, p):
        return sum(m.x[p, a] for a in aas) <= 1

    model.peak_con = pyo.Constraint(peaks, rule=peak_rule)

    # Each amino acid used by at most one peak
    def aa_rule(m, a):
        return sum(m.x[p, a] for p in peaks) <= 1

    model.aa_con = pyo.Constraint(aas, rule=aa_rule)

    # Exactly required number of assignments
    def count_rule(m):
        return sum(m.x[p, a] for p in peaks for a in aas) == num_assignments_required

    model.count_con = pyo.Constraint(rule=count_rule)

    # NOE constraints
    def noe_rule(m, i):
        (p1, a1), (p2, a2) = noe_forbidden_pairs[i]
        return m.x[p1, a1] + m.x[p2, a2] <= 1

    model.noe_con = pyo.Constraint(
        range(len(noe_forbidden_pairs)), rule=noe_rule
    )

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}