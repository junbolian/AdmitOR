# IR: {"sets":{"P":[0,1,2,3,4],"A":[0,1,2,3,4,5],"R":[[0,4],[1,2]]},"params":{"c[p,a]":"params['cost_matrix'][p][a], real","K":"params['exact_assignments'], nonnegative integer","n[a,b]":"params['noe_parameters'][a][b], binary"},"variables":{"x[p,a]":"binary"},"constraints":["sum(a in A, x[p,a]) <= 1 for p in P","sum(p in P, x[p,a]) <= 1 for a in A","sum(p in P, a in A, x[p,a]) == K","x[p,a] + x[q,b] <= 2 - n[a,b] for (p,q) in R and a,b in A"],"objective":"minimize sum(p in P, a in A, c[p,a]*x[p,a])"}
#
# Missing required parameters produce a failure result; NOE data cannot
# be inferred or replaced with invented numeric values.
# The two stated peak pairs define R; n[a,b] = 1 activates a conflict.
# Matrix inputs support nested sequences, nested integer-keyed mappings,
# or mappings keyed by (row, column) tuples.

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _matrix_entry(matrix, row, column):
    if isinstance(matrix, Mapping) and (row, column) in matrix:
        return matrix[(row, column)]
    return matrix[row][column]


def solve(params):
    required_parameters = (
        "cost_matrix",
        "exact_assignments",
        "noe_parameters",
    )
    for parameter_name in required_parameters:
        if parameter_name not in params:
            return {
                "objective": None,
                "status": f"missing_parameter:{parameter_name}",
            }

    cost_matrix = params["cost_matrix"]
    exact_assignments = params["exact_assignments"]
    noe_parameters = params["noe_parameters"]

    model = pyo.ConcreteModel()

    model.peaks = pyo.Set(initialize=range(5), ordered=True)
    model.amino_acids = pyo.Set(initialize=range(6), ordered=True)
    model.restricted_peak_pairs = pyo.Set(
        dimen=2,
        initialize=[(0, 4), (1, 2)],
        ordered=True,
    )

    model.assignment_cost = pyo.Param(
        model.peaks,
        model.amino_acids,
        initialize=lambda instance, peak, acid: _matrix_entry(
            cost_matrix, peak, acid
        ),
        within=pyo.Reals,
    )
    model.required_assignments = pyo.Param(
        initialize=exact_assignments,
        within=pyo.NonNegativeIntegers,
    )
    model.noe_indicator = pyo.Param(
        model.amino_acids,
        model.amino_acids,
        initialize=lambda instance, acid_a, acid_b: _matrix_entry(
            noe_parameters, acid_a, acid_b
        ),
        within=pyo.Binary,
    )

    model.assignment = pyo.Var(
        model.peaks,
        model.amino_acids,
        domain=pyo.Binary,
    )

    def peak_capacity_rule(instance, peak):
        return sum(
            instance.assignment[peak, acid]
            for acid in instance.amino_acids
        ) <= 1

    model.peak_capacity = pyo.Constraint(
        model.peaks,
        rule=peak_capacity_rule,
    )

    def amino_acid_capacity_rule(instance, acid):
        return sum(
            instance.assignment[peak, acid]
            for peak in instance.peaks
        ) <= 1

    model.amino_acid_capacity = pyo.Constraint(
        model.amino_acids,
        rule=amino_acid_capacity_rule,
    )

    model.assignment_total = pyo.Constraint(
        expr=sum(
            model.assignment[peak, acid]
            for peak in model.peaks
            for acid in model.amino_acids
        ) == model.required_assignments
    )

    def noe_conflict_rule(instance, peak_a, peak_b, acid_a, acid_b):
        return (
            instance.assignment[peak_a, acid_a]
            + instance.assignment[peak_b, acid_b]
            <= 2 - instance.noe_indicator[acid_a, acid_b]
        )

    model.noe_conflicts = pyo.Constraint(
        model.restricted_peak_pairs,
        model.amino_acids,
        model.amino_acids,
        rule=noe_conflict_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[peak, acid]
            * model.assignment[peak, acid]
            for peak in model.peaks
            for acid in model.amino_acids
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}