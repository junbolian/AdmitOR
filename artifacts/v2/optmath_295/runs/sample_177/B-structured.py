# IR: {"sets":{"P":"range(params['num_peaks'])","A":"range(params['num_amino_acids'])","F":[]},"params":{"num_peaks":"params['num_peaks']; frozen at 4","num_amino_acids":"params['num_amino_acids']; frozen at 5","num_assignments":"params['num_assignments']","cost[p,a]":"params[f'cost_peak{p}_aa{a}']"},"variables":{"x[p,a]":"binary"},"constraints":["sum(x[p,a] for a in A) <= 1 for each p in P","sum(x[p,a] for p in P) <= 1 for each a in A","sum(x[p,a] for p in P for a in A) == num_assignments","x[p,a] + x[q,b] <= 1 for each (p,q,a,b) in F"],"objective":"minimize sum(cost[p,a]*x[p,a] for p in P for a in A)","scope":"NOE-related peak pairs, distances, and threshold are unspecified. F is empty, so this solves the assignment relaxation; its objective is not a verified optimum of the unspecified full NOE problem."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the assignment model determined by the supplied parameters.

    The statement provides no concrete NOE incompatibilities or distance
    data. Consequently, no specific NOE restrictions can be reconstructed.
    This implementation solves the assignment relaxation without requiring
    additional parameter keys or inventing restrictions.
    """
    num_peaks = params["num_peaks"]
    num_amino_acids = params["num_amino_acids"]
    num_assignments = params["num_assignments"]

    costs = {
        (peak, amino_acid): params[f"cost_peak{peak}_aa{amino_acid}"]
        for peak in range(4)
        for amino_acid in range(5)
    }

    if num_peaks != 4 or num_amino_acids != 5:
        return {"objective": None, "status": "invalid_frozen_set_sizes"}

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=range(int(num_peaks)), ordered=True)
    model.A = pyo.Set(initialize=range(int(num_amino_acids)), ordered=True)

    # No forbidden assignment combinations are specified in the input.
    model.F = pyo.Set(dimen=4, initialize=[], ordered=True)

    model.assignment_cost = pyo.Param(
        model.P,
        model.A,
        initialize=costs,
        within=pyo.Reals,
    )
    model.required_assignments = pyo.Param(
        initialize=num_assignments,
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.P, model.A, domain=pyo.Binary)

    def peak_capacity_rule(instance, peak):
        return sum(
            instance.x[peak, amino_acid]
            for amino_acid in instance.A
        ) <= 1

    model.peak_capacity = pyo.Constraint(
        model.P,
        rule=peak_capacity_rule,
    )

    def amino_acid_capacity_rule(instance, amino_acid):
        return sum(
            instance.x[peak, amino_acid]
            for peak in instance.P
        ) <= 1

    model.amino_acid_capacity = pyo.Constraint(
        model.A,
        rule=amino_acid_capacity_rule,
    )

    model.assignment_count = pyo.Constraint(
        expr=sum(
            model.x[peak, amino_acid]
            for peak in model.P
            for amino_acid in model.A
        ) == model.required_assignments
    )

    def noe_compatibility_rule(
        instance, peak, other_peak, amino_acid, other_amino_acid
    ):
        return (
            instance.x[peak, amino_acid]
            + instance.x[other_peak, other_amino_acid]
            <= 1
        )

    model.noe_compatibility = pyo.Constraint(
        model.F,
        rule=noe_compatibility_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[peak, amino_acid]
            * model.x[peak, amino_acid]
            for peak in model.P
            for amino_acid in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}