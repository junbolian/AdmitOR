# IR: {"sets":{"peaks":[0,1,2,3,4],"amino_acids":[0,1,2,3,4,5],"restricted_peak_pairs":[[0,4],[1,2]]},"params":{"cost_matrix":"required 5x6 matrix read from params","exact_assignments":"required nonnegative integer read from params","noe_parameters":"optional 6x6 binary matrix read from params when supplied; if absent, enforce only the two explicitly stated incompatibilities"},"decision_variables":{"assignment[p,a]":"binary"},"constraints":["For each peak p: sum_a assignment[p,a] <= 1","For each amino acid a: sum_p assignment[p,a] <= 1","sum_(p,a) assignment[p,a] == exact_assignments","If noe_parameters is supplied: for each restricted peak pair (p,q) and amino-acid pair (a,b), assignment[p,a] + assignment[q,b] <= 2 - noe_parameters[a,b]","Otherwise: assignment[0,0] + assignment[4,1] <= 1 and assignment[1,0] + assignment[2,1] <= 1"],"objective":"minimize sum_(p,a) cost_matrix[p,a] * assignment[p,a]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    exact_assignments = params["exact_assignments"]

    # Without NOE data, the only specified restrictions are the two examples.
    noe_parameters = (
        params["noe_parameters"] if "noe_parameters" in params else None
    )

    model = pyo.ConcreteModel()

    model.peaks = pyo.RangeSet(0, 4)
    model.amino_acids = pyo.RangeSet(0, 5)
    model.restricted_peak_pairs = pyo.Set(
        dimen=2, initialize=[(0, 4), (1, 2)]
    )

    model.assignment_cost = pyo.Param(
        model.peaks,
        model.amino_acids,
        initialize={
            (peak, amino_acid): cost_matrix[peak][amino_acid]
            for peak in model.peaks
            for amino_acid in model.amino_acids
        },
        within=pyo.Reals,
    )

    model.required_assignments = pyo.Param(
        initialize=exact_assignments,
        within=pyo.NonNegativeIntegers,
    )

    model.assignment = pyo.Var(
        model.peaks, model.amino_acids, domain=pyo.Binary
    )

    def peak_capacity_rule(current_model, peak):
        return sum(
            current_model.assignment[peak, amino_acid]
            for amino_acid in current_model.amino_acids
        ) <= 1

    model.peak_capacity = pyo.Constraint(
        model.peaks, rule=peak_capacity_rule
    )

    def amino_acid_capacity_rule(current_model, amino_acid):
        return sum(
            current_model.assignment[peak, amino_acid]
            for peak in current_model.peaks
        ) <= 1

    model.amino_acid_capacity = pyo.Constraint(
        model.amino_acids, rule=amino_acid_capacity_rule
    )

    model.assignment_total = pyo.Constraint(
        expr=sum(
            model.assignment[peak, amino_acid]
            for peak in model.peaks
            for amino_acid in model.amino_acids
        ) == model.required_assignments
    )

    if noe_parameters is not None:
        model.noe_active = pyo.Param(
            model.amino_acids,
            model.amino_acids,
            initialize={
                (first_aa, second_aa): noe_parameters[first_aa][second_aa]
                for first_aa in model.amino_acids
                for second_aa in model.amino_acids
            },
            within=pyo.Binary,
        )

        def noe_restriction_rule(
            current_model, first_peak, second_peak, first_aa, second_aa
        ):
            return (
                current_model.assignment[first_peak, first_aa]
                + current_model.assignment[second_peak, second_aa]
                <= 2 - current_model.noe_active[first_aa, second_aa]
            )

        model.noe_restrictions = pyo.Constraint(
            model.restricted_peak_pairs,
            model.amino_acids,
            model.amino_acids,
            rule=noe_restriction_rule,
        )
    else:
        def explicit_restriction_rule(
            current_model, first_peak, second_peak
        ):
            return (
                current_model.assignment[first_peak, 0]
                + current_model.assignment[second_peak, 1]
                <= 1
            )

        model.noe_restrictions = pyo.Constraint(
            model.restricted_peak_pairs,
            rule=explicit_restriction_rule,
        )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[peak, amino_acid]
            * model.assignment[peak, amino_acid]
            for peak in model.peaks
            for amino_acid in model.amino_acids
        ),
        sense=pyo.minimize,
    )

    solve_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        solve_failed = True

    # Objective availability is the sole success criterion.
    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": (
                "infeasible_or_failed"
                if solve_failed
                else "objective_unavailable"
            ),
        }

    return {"objective": obj_val, "status": "optimal"}