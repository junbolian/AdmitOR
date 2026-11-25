# IR: {"sets":{"P":"range(params['num_peaks'])","A":"range(params['num_amino_acids'])","N":"complete set of 24 NOE conflict tuples (i,j,k,l), unavailable in the stated inputs"},"params":{"assignment_cost":"cost matrix on P x A","num_assignments_required":"exact assignment count","num_peaks":"peak count","num_amino_acids":"amino-acid count"},"decision_variables":{"x[i,j]":"binary, for (i,j) in P x A"},"constraints":["sum_j x[i,j] <= 1 for each i in P","sum_i x[i,j] <= 1 for each j in A","sum_i sum_j x[i,j] == num_assignments_required","x[i,j] + x[k,l] <= 1 for each (i,j,k,l) in N"],"objective":"minimize sum_i sum_j assignment_cost[i][j]*x[i,j]","data_requirement":"Twenty of the 24 NOE conflicts are unspecified. Return incomplete_noe_data unless the complete conflict set is supplied through the optional supplemental input params['noe_conflicts']."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # The previous failure reflects missing problem data, not a solver defect.
    # Neither assignment costs nor the required number of assignments identifies
    # the twenty omitted NOE conflicts. Inventing them, or solving with only the
    # four stated conflicts, would solve a different optimization problem.
    assignment_cost = params["assignment_cost"]
    num_assignments_required = params["num_assignments_required"]
    num_peaks = params["num_peaks"]
    num_amino_acids = params["num_amino_acids"]

    # This supplemental input is necessary because the stated four parameters
    # do not contain the complete NOE constraint structure.
    if "noe_conflicts" not in params:
        return {"objective": None, "status": "incomplete_noe_data"}

    peak_indices = range(num_peaks)
    amino_acid_indices = range(num_amino_acids)
    supplied_conflicts = list(params["noe_conflicts"])

    if len(supplied_conflicts) != 24:
        return {"objective": None, "status": "expected_24_noe_conflicts"}

    conflicts = set()
    for conflict in supplied_conflicts:
        if not isinstance(conflict, (tuple, list)) or len(conflict) != 4:
            return {"objective": None, "status": "invalid_noe_conflict"}

        peak_i, acid_j, peak_k, acid_l = conflict
        indices = (peak_i, acid_j, peak_k, acid_l)
        if any(
            not isinstance(value, int) or isinstance(value, bool)
            for value in indices
        ):
            return {"objective": None, "status": "invalid_noe_index"}

        if (
            peak_i not in peak_indices
            or peak_k not in peak_indices
            or acid_j not in amino_acid_indices
            or acid_l not in amino_acid_indices
        ):
            return {"objective": None, "status": "invalid_noe_index"}

        first, second = sorted(((peak_i, acid_j), (peak_k, acid_l)))
        conflicts.add(first + second)

    if len(conflicts) != 24:
        return {"objective": None, "status": "duplicate_noe_conflicts"}

    stated_conflicts = {
        (0, 0, 3, 3),
        (0, 0, 3, 4),
        (0, 1, 3, 3),
        (0, 1, 3, 4),
    }
    if not stated_conflicts.issubset(conflicts):
        return {"objective": None, "status": "missing_stated_noe_conflicts"}

    model = pyo.ConcreteModel()

    model.peaks = pyo.Set(initialize=peak_indices, ordered=True)
    model.amino_acids = pyo.Set(initialize=amino_acid_indices, ordered=True)
    model.noe_pairs = pyo.Set(
        dimen=4,
        initialize=sorted(conflicts),
        ordered=True,
    )

    model.cost = pyo.Param(
        model.peaks,
        model.amino_acids,
        initialize=lambda mdl, peak, acid: assignment_cost[peak][acid],
        within=pyo.Reals,
    )
    model.required_assignments = pyo.Param(
        initialize=num_assignments_required,
        within=pyo.Integers,
    )

    model.x = pyo.Var(
        model.peaks,
        model.amino_acids,
        domain=pyo.Binary,
    )

    def peak_limit_rule(mdl, peak):
        return (
            pyo.quicksum(mdl.x[peak, acid] for acid in mdl.amino_acids)
            <= 1
        )

    model.peak_limits = pyo.Constraint(
        model.peaks,
        rule=peak_limit_rule,
    )

    def amino_acid_limit_rule(mdl, acid):
        return (
            pyo.quicksum(mdl.x[peak, acid] for peak in mdl.peaks)
            <= 1
        )

    model.amino_acid_limits = pyo.Constraint(
        model.amino_acids,
        rule=amino_acid_limit_rule,
    )

    model.assignment_count = pyo.Constraint(
        expr=pyo.quicksum(
            model.x[peak, acid]
            for peak in model.peaks
            for acid in model.amino_acids
        )
        == model.required_assignments
    )

    def noe_rule(mdl, peak_i, acid_j, peak_k, acid_l):
        return mdl.x[peak_i, acid_j] + mdl.x[peak_k, acid_l] <= 1

    model.noe_constraints = pyo.Constraint(
        model.noe_pairs,
        rule=noe_rule,
    )

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.cost[peak, acid] * model.x[peak, acid]
            for peak in model.peaks
            for acid in model.amino_acids
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}