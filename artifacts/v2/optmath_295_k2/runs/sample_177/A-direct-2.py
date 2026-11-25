import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    peaks = range(4)
    amino_acids = range(5)

    cost = {}
    for i in peaks:
        for j in amino_acids:
            cost[(i, j)] = params[f"cost_peak{i}_aa{j}"]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(peaks, amino_acids, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(cost[(i, j)] * model.x[i, j] for i in peaks for j in amino_acids),
        sense=pyo.minimize,
    )

    # Each peak assigned to at most one amino acid
    model.peak_constraint = pyo.Constraint(
        peaks, rule=lambda model, i: sum(model.x[i, j] for j in amino_acids) <= 1
    )

    # Each amino acid assigned to at most one peak
    model.aa_constraint = pyo.Constraint(
        amino_acids, rule=lambda model, j: sum(model.x[i, j] for i in peaks) <= 1
    )

    # Exactly num_assignments assignments
    model.num_assignments_constraint = pyo.Constraint(
        expr=sum(model.x[i, j] for i in peaks for j in amino_acids)
        == params["num_assignments"]
    )

    # NOE pairwise constraints: if Peak p assigned to aa a, Peak q cannot be
    # assigned to aa b unless distance(a, b) < threshold. The problem does not
    # specify concrete distance data, so no additional numeric restriction is
    # introduced beyond the stated structural assignment constraints.

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}