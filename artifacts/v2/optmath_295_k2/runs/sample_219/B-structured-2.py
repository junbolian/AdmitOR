# IR: {"sets":{"I":[0,1,2,3],"J":[0,1,2,3,4],"P":"[(j,l) for j in J for l in J if l<j]"},"params":{"cost_matrix":"4x5 assignment costs","total_assignments":"exact assignment count","noe_thresholds":"10 numerical NOE upper bounds in P order, or a 5x5 matrix indexed by (j,l)"},"variables":{"x[i,j]":"Binary"},"constraints":["For each j in J: sum_i x[i,j] <= 1","For each i in I: sum_j x[i,j] <= 1","sum_i,j x[i,j] == total_assignments","For each (j,l) in P: x[1,j] + x[3,l] <= noe_bound[j,l]"],"objective":"minimize sum_i,j cost_matrix[i][j]*x[i,j]"}
#
# Modeling assumption required by the incomplete NOE specification:
# numerical noe_thresholds are upper bounds on the assignment-pair sums.
# The pair order is (1,0), (2,0), (2,1), (3,0), (3,1), (3,2),
# (4,0), (4,1), (4,2), (4,3), matching the examples in the prompt.
# Physical distance comparisons cannot be reconstructed from thresholds alone.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    total_assignments = params["total_assignments"]
    noe_thresholds = params["noe_thresholds"]

    peak_indices = range(4)
    amino_acid_indices = range(5)
    noe_pairs = [
        (first_acid, second_acid)
        for first_acid in amino_acid_indices
        for second_acid in amino_acid_indices
        if second_acid < first_acid
    ]

    try:
        threshold_count = len(noe_thresholds)
    except TypeError:
        return {"objective": None, "status": "invalid_noe_shape"}

    if threshold_count == len(noe_pairs):
        noe_bounds = {
            pair: noe_thresholds[position]
            for position, pair in enumerate(noe_pairs)
        }
    elif threshold_count == len(amino_acid_indices):
        try:
            matrix_shape_valid = all(
                len(noe_thresholds[acid]) == len(amino_acid_indices)
                for acid in amino_acid_indices
            )
        except TypeError:
            matrix_shape_valid = False

        if not matrix_shape_valid:
            return {"objective": None, "status": "invalid_noe_shape"}

        noe_bounds = {
            (first_acid, second_acid):
                noe_thresholds[first_acid][second_acid]
            for first_acid, second_acid in noe_pairs
        }
    else:
        return {"objective": None, "status": "invalid_noe_shape"}

    model = pyo.ConcreteModel()

    model.peaks = pyo.Set(initialize=peak_indices, ordered=True)
    model.amino_acids = pyo.Set(
        initialize=amino_acid_indices, ordered=True
    )
    model.noe_pairs = pyo.Set(
        dimen=2, initialize=noe_pairs, ordered=True
    )

    model.assignment_cost = pyo.Param(
        model.peaks,
        model.amino_acids,
        initialize=lambda mod, peak, acid: cost_matrix[peak][acid],
        within=pyo.Reals,
    )
    model.required_assignments = pyo.Param(
        initialize=total_assignments,
        within=pyo.Reals,
    )
    model.noe_bound = pyo.Param(
        model.noe_pairs,
        initialize=noe_bounds,
        within=pyo.Reals,
    )

    model.x = pyo.Var(
        model.peaks, model.amino_acids, domain=pyo.Binary
    )

    def amino_acid_capacity_rule(mod, acid):
        return sum(mod.x[peak, acid] for peak in mod.peaks) <= 1

    model.amino_acid_capacity = pyo.Constraint(
        model.amino_acids, rule=amino_acid_capacity_rule
    )

    def peak_capacity_rule(mod, peak):
        return sum(
            mod.x[peak, acid] for acid in mod.amino_acids
        ) <= 1

    model.peak_capacity = pyo.Constraint(
        model.peaks, rule=peak_capacity_rule
    )

    model.assignment_count = pyo.Constraint(
        expr=sum(
            model.x[peak, acid]
            for peak in model.peaks
            for acid in model.amino_acids
        ) == model.required_assignments
    )

    def noe_consistency_rule(mod, first_acid, second_acid):
        return (
            mod.x[1, first_acid] + mod.x[3, second_acid]
            <= mod.noe_bound[first_acid, second_acid]
        )

    model.noe_consistency = pyo.Constraint(
        model.noe_pairs, rule=noe_consistency_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[peak, acid] * model.x[peak, acid]
            for peak in model.peaks
            for acid in model.amino_acids
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}