import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    assignment_cost = params["assignment_cost"]
    required_assignments = params["required_assignments"]

    n_peaks = 5
    n_amino = 6

    model = pyo.ConcreteModel()

    model.PEAKS = pyo.RangeSet(0, n_peaks - 1)
    model.AMINO = pyo.RangeSet(0, n_amino - 1)

    model.x = pyo.Var(model.PEAKS, model.AMINO, domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(
            assignment_cost[i][j] * mdl.x[i, j]
            for i in range(n_peaks)
            for j in range(n_amino)
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each peak assigned to at most one amino acid
    def peak_rule(mdl, i):
        return sum(mdl.x[i, j] for j in range(n_amino)) <= 1

    model.peak_constraint = pyo.Constraint(model.PEAKS, rule=peak_rule)

    # Each amino acid assigned to at most one peak
    def amino_rule(mdl, j):
        return sum(mdl.x[i, j] for i in range(n_peaks)) <= 1

    model.amino_constraint = pyo.Constraint(model.AMINO, rule=amino_rule)

    # Exactly required_assignments assignments
    def total_rule(mdl):
        return sum(
            mdl.x[i, j] for i in range(n_peaks) for j in range(n_amino)
        ) == required_assignments

    model.total_constraint = pyo.Constraint(rule=total_rule)

    # NOE constraints: x[i1,j1] + x[i2,j2] <= 1
    # Derived from LP data:
    #   NOE_0_4_0_1: x[0,0] + x[4,1] <= 1
    #   plus symmetric pairs for amino acids 1, 3, 4 with peaks 0 and 4
    #   NOE_1_2_0_1: x[1,0] + x[2,1] <= 1
    #   plus symmetric pairs for amino acids 1, 3, 4 with peaks 1 and 2
    noe_pairs = []
    for jj in (1, 3, 4):
        noe_pairs.append((0, 0, 4, jj))
        noe_pairs.append((1, 0, 2, jj))

    model.NOE = pyo.Set(initialize=list(range(len(noe_pairs))), ordered=True)

    def noe_rule(mdl, k):
        i1, j1, i2, j2 = noe_pairs[k]
        return mdl.x[i1, j1] + mdl.x[i2, j2] <= 1

    model.noe_constraint = pyo.Constraint(model.NOE, rule=noe_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception as exc:
        return {"objective": None, "status": "infeasible_or_error: " + str(type(exc).__name__)}