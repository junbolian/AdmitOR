# IR: {"sets":{"peaks":[0,1,2,3],"amino_acids":[0,1,2,3,4],"noe_exclusions":[[0,0,1,2],[0,0,1,3],[0,0,1,4],[0,1,1,2],[0,1,1,3],[0,1,1,4]]},"params":{"cost_peak{p}_aa{a}":"real cost for every (p,a) in peaks x amino_acids","num_assignments_required":"exact total assignments"},"variables":{"assignment[p,a]":"binary"},"constraints":["sum_a assignment[p,a] <= 1 for each peak p","sum_p assignment[p,a] <= 1 for each amino acid a","sum_(p,a) assignment[p,a] == num_assignments_required","assignment[p,a] + assignment[q,b] <= 1 for each (p,a,q,b) in noe_exclusions"],"objective":"minimize sum_(p,a) cost_peak{p}_aa{a} * assignment[p,a]"}
# The problem supplies only six explicit NOE exclusions. Those are modeled
# below; the unspecified "similar restrictions" cannot be inferred.
# Dependencies: pyomo and highspy.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.peaks = pyo.Set(initialize=range(4), ordered=True)
    model.amino_acids = pyo.Set(initialize=range(5), ordered=True)

    assignment_costs = {
        (0, 0): params["cost_peak0_aa0"],
        (0, 1): params["cost_peak0_aa1"],
        (0, 2): params["cost_peak0_aa2"],
        (0, 3): params["cost_peak0_aa3"],
        (0, 4): params["cost_peak0_aa4"],
        (1, 0): params["cost_peak1_aa0"],
        (1, 1): params["cost_peak1_aa1"],
        (1, 2): params["cost_peak1_aa2"],
        (1, 3): params["cost_peak1_aa3"],
        (1, 4): params["cost_peak1_aa4"],
        (2, 0): params["cost_peak2_aa0"],
        (2, 1): params["cost_peak2_aa1"],
        (2, 2): params["cost_peak2_aa2"],
        (2, 3): params["cost_peak2_aa3"],
        (2, 4): params["cost_peak2_aa4"],
        (3, 0): params["cost_peak3_aa0"],
        (3, 1): params["cost_peak3_aa1"],
        (3, 2): params["cost_peak3_aa2"],
        (3, 3): params["cost_peak3_aa3"],
        (3, 4): params["cost_peak3_aa4"],
    }

    model.assignment_cost = pyo.Param(
        model.peaks,
        model.amino_acids,
        initialize=assignment_costs,
        within=pyo.Reals,
    )
    model.required_assignments = pyo.Param(
        initialize=params["num_assignments_required"],
        within=pyo.Reals,
    )
    model.noe_exclusions = pyo.Set(
        dimen=4,
        initialize=[
            (0, 0, 1, 2),
            (0, 0, 1, 3),
            (0, 0, 1, 4),
            (0, 1, 1, 2),
            (0, 1, 1, 3),
            (0, 1, 1, 4),
        ],
    )

    model.assignment = pyo.Var(
        model.peaks, model.amino_acids, domain=pyo.Binary
    )

    def peak_capacity_rule(instance, peak):
        return sum(
            instance.assignment[peak, amino_acid]
            for amino_acid in instance.amino_acids
        ) <= 1

    model.peak_capacity = pyo.Constraint(
        model.peaks, rule=peak_capacity_rule
    )

    def amino_acid_capacity_rule(instance, amino_acid):
        return sum(
            instance.assignment[peak, amino_acid]
            for peak in instance.peaks
        ) <= 1

    model.amino_acid_capacity = pyo.Constraint(
        model.amino_acids, rule=amino_acid_capacity_rule
    )

    model.assignment_count = pyo.Constraint(
        expr=sum(
            model.assignment[peak, amino_acid]
            for peak in model.peaks
            for amino_acid in model.amino_acids
        ) == model.required_assignments
    )

    def noe_exclusion_rule(
        instance, first_peak, first_amino_acid, second_peak, second_amino_acid
    ):
        return (
            instance.assignment[first_peak, first_amino_acid]
            + instance.assignment[second_peak, second_amino_acid]
            <= 1
        )

    model.noe_compatibility = pyo.Constraint(
        model.noe_exclusions, rule=noe_exclusion_rule
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

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        # Unexpected runtime errors remain visible to the caller.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}