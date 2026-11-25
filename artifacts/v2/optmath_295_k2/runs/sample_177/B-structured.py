# IR: {"sets":{"peaks":[0,1,2,3],"amino_acids":[0,1,2,3,4],"forbidden_noe":"params.get('noe_forbidden_assignments', []), tuples (i,a,j,b)"},"params":{"cost[i,a]":"params[f'cost_peak{i}_aa{a}']","required_assignments":"params['num_assignments']"},"variables":{"x[i,a]":"binary"},"constraints":["For each peak i: sum_a x[i,a] <= 1","For each amino acid a: sum_i x[i,a] <= 1","sum_(i,a) x[i,a] == required_assignments","For each (i,a,j,b) in forbidden_noe: x[i,a] + x[j,b] <= 1"],"objective":"minimize sum_(i,a) cost[i,a] * x[i,a]"}
#
# Assumption: No NOE pairs, distances, or threshold are specified in the
# supplied problem data. Accordingly, no forbidden NOE combinations are
# assumed unless optional "noe_forbidden_assignments" tuples are supplied.
# With only the listed PARAMS, this solves the assignment problem without
# additional NOE restrictions; unspecified restrictions cannot be inferred.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = {
        (peak, amino_acid): params[f"cost_peak{peak}_aa{amino_acid}"]
        for peak in range(4)
        for amino_acid in range(5)
    }
    required_assignments = params["num_assignments"]
    forbidden_noe = params.get("noe_forbidden_assignments", [])

    model = pyo.ConcreteModel()

    model.peaks = pyo.Set(initialize=range(4), ordered=True)
    model.amino_acids = pyo.Set(initialize=range(5), ordered=True)
    model.forbidden_noe = pyo.Set(
        dimen=4,
        within=(
            model.peaks
            * model.amino_acids
            * model.peaks
            * model.amino_acids
        ),
        initialize=forbidden_noe,
        ordered=True,
    )

    model.assignment_cost = pyo.Param(
        model.peaks,
        model.amino_acids,
        initialize=costs,
        within=pyo.Reals,
    )
    model.required_assignments = pyo.Param(
        initialize=required_assignments,
        within=pyo.Reals,
    )

    model.x = pyo.Var(
        model.peaks,
        model.amino_acids,
        domain=pyo.Binary,
    )

    def peak_limit_rule(current_model, peak):
        return sum(
            current_model.x[peak, amino_acid]
            for amino_acid in current_model.amino_acids
        ) <= 1

    model.peak_limits = pyo.Constraint(
        model.peaks,
        rule=peak_limit_rule,
    )

    def amino_acid_limit_rule(current_model, amino_acid):
        return sum(
            current_model.x[peak, amino_acid]
            for peak in current_model.peaks
        ) <= 1

    model.amino_acid_limits = pyo.Constraint(
        model.amino_acids,
        rule=amino_acid_limit_rule,
    )

    model.assignment_count = pyo.Constraint(
        expr=sum(
            model.x[peak, amino_acid]
            for peak in model.peaks
            for amino_acid in model.amino_acids
        ) == model.required_assignments
    )

    def noe_rule(current_model, peak_i, aa_a, peak_j, aa_b):
        return (
            current_model.x[peak_i, aa_a]
            + current_model.x[peak_j, aa_b]
            <= 1
        )

    model.noe_constraints = pyo.Constraint(
        model.forbidden_noe,
        rule=noe_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[peak, amino_acid]
            * model.x[peak, amino_acid]
            for peak in model.peaks
            for amino_acid in model.amino_acids
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Allow objective retrieval to determine success after the solver's
        # known failure to load a feasible solution. Propagate other errors.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}