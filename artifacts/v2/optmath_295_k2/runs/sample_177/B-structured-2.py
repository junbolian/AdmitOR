# {
#   "sets": {"P": [0,1,2,3], "A": [0,1,2,3,4], "F": "optional params['noe_forbidden_assignments']; defaults to []"},
#   "params": {"cost_peak{p}_aa{a}": "params cost for each (p,a) in P x A", "num_assignments": "params exact assignment count"},
#   "variables": {"x[p,a]": "binary for each (p,a) in P x A"},
#   "constraints": [
#     "For each p in P: sum(x[p,a] for a in A) <= 1",
#     "For each a in A: sum(x[p,a] for p in P) <= 1",
#     "sum(x[p,a] for p in P for a in A) == num_assignments",
#     "For each (p,a,q,b) in F: x[p,a] + x[q,b] <= 1"
#   ],
#   "objective": "minimize sum(cost_peak{p}_aa{a} * x[p,a] for p in P for a in A)"
# }
#
# The statement supplies no NOE peak pairs, distances, or threshold.
# Therefore, with only the listed parameters, this solves the assignment
# model without additional NOE restrictions. It cannot certify compatibility
# with unspecified NOE restrictions. Optional forbidden assignment tuples
# (peak, amino_acid, other_peak, other_amino_acid) are enforced if supplied.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    peaks = range(4)
    amino_acids = range(5)

    assignment_costs = {
        (peak, amino_acid): params[f"cost_peak{peak}_aa{amino_acid}"]
        for peak in peaks
        for amino_acid in amino_acids
    }
    required_assignments = params["num_assignments"]

    forbidden_assignments = tuple(
        tuple(entry)
        for entry in params.get("noe_forbidden_assignments", ())
    )

    for entry in forbidden_assignments:
        if len(entry) != 4:
            raise ValueError(
                "Each forbidden assignment must contain (p, a, q, b)."
            )
        peak, amino_acid, other_peak, other_amino_acid = entry
        if (
            peak not in peaks
            or other_peak not in peaks
            or amino_acid not in amino_acids
            or other_amino_acid not in amino_acids
            or peak == other_peak
        ):
            raise ValueError(
                "Forbidden assignments must reference two distinct valid "
                "peaks and valid amino acids."
            )

    model = pyo.ConcreteModel()

    model.Peaks = pyo.Set(initialize=peaks, ordered=True)
    model.AminoAcids = pyo.Set(initialize=amino_acids, ordered=True)
    model.ForbiddenAssignments = pyo.Set(
        dimen=4,
        initialize=forbidden_assignments,
    )

    model.assignment_cost = pyo.Param(
        model.Peaks,
        model.AminoAcids,
        initialize=assignment_costs,
        within=pyo.Reals,
    )
    model.required_assignments = pyo.Param(
        initialize=required_assignments,
        within=pyo.Reals,
    )

    model.x = pyo.Var(
        model.Peaks,
        model.AminoAcids,
        domain=pyo.Binary,
    )

    def peak_limit_rule(instance, peak):
        return sum(
            instance.x[peak, amino_acid]
            for amino_acid in instance.AminoAcids
        ) <= 1

    model.peak_limit = pyo.Constraint(
        model.Peaks,
        rule=peak_limit_rule,
    )

    def amino_acid_limit_rule(instance, amino_acid):
        return sum(
            instance.x[peak, amino_acid]
            for peak in instance.Peaks
        ) <= 1

    model.amino_acid_limit = pyo.Constraint(
        model.AminoAcids,
        rule=amino_acid_limit_rule,
    )

    model.assignment_count = pyo.Constraint(
        expr=sum(
            model.x[peak, amino_acid]
            for peak in model.Peaks
            for amino_acid in model.AminoAcids
        ) == model.required_assignments
    )

    def noe_rule(instance, peak, amino_acid, other_peak, other_amino_acid):
        return (
            instance.x[peak, amino_acid]
            + instance.x[other_peak, other_amino_acid]
            <= 1
        )

    model.noe_compatibility = pyo.Constraint(
        model.ForbiddenAssignments,
        rule=noe_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[peak, amino_acid]
            * model.x[peak, amino_acid]
            for peak in model.Peaks
            for amino_acid in model.AminoAcids
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}