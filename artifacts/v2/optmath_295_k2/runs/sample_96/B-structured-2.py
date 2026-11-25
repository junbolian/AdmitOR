# IR: {"sets":{"P":"range(params['peak_count'])","AA":"range(params['amino_acid_count'])"},"params":{"assignment_cost":"complete numeric cost matrix indexed [peak][amino_acid]; required, never inferred","noe_rhs_peak1_aa1_peak2_aa0":"first NOE RHS","noe_rhs_peak1_aa3_peak2_aa0":"second NOE RHS","num_assignments":"exact assignment count","peak_count":"frozen peak set size","amino_acid_count":"frozen amino acid set size"},"decision_variables":{"x[p,a]":"Binary for p in P, a in AA"},"constraints":["sum(x[p,a] for a in AA) <= 1 for each p in P","sum(x[p,a] for p in P) <= 1 for each a in AA","sum(x[p,a] for p in P for a in AA) == num_assignments","x[1,1] + x[2,0] <= noe_rhs_peak1_aa1_peak2_aa0","x[1,3] + x[2,0] <= noe_rhs_peak1_aa3_peak2_aa0"],"objective":"minimize sum(assignment_cost[p][a] * x[p,a] for p in P for a in AA)","failure_handling":"return missing_<parameter> for absent required inputs; determine solve success only by objective retrieval"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the assignment model, returning a short reason for missing inputs."""
    # Row bounds and selected entries do not determine the missing costs.
    # Report an absent matrix instead of fabricating an optimization instance.
    required_keys = (
        "assignment_cost",
        "noe_rhs_peak1_aa1_peak2_aa0",
        "noe_rhs_peak1_aa3_peak2_aa0",
        "num_assignments",
        "peak_count",
        "amino_acid_count",
    )
    for key in required_keys:
        if key not in params:
            return {"objective": None, "status": f"missing_{key}"}

    assignment_cost = params["assignment_cost"]
    noe_rhs_first = params["noe_rhs_peak1_aa1_peak2_aa0"]
    noe_rhs_second = params["noe_rhs_peak1_aa3_peak2_aa0"]
    num_assignments = params["num_assignments"]
    peak_count = params["peak_count"]
    amino_acid_count = params["amino_acid_count"]

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=range(peak_count), ordered=True)
    model.AA = pyo.Set(initialize=range(amino_acid_count), ordered=True)

    model.cost = pyo.Param(
        model.P,
        model.AA,
        initialize={
            (peak, amino_acid): assignment_cost[peak][amino_acid]
            for peak in model.P
            for amino_acid in model.AA
        },
        within=pyo.Reals,
    )
    model.required_assignments = pyo.Param(
        initialize=num_assignments, within=pyo.Reals
    )
    model.noe_limit_first = pyo.Param(
        initialize=noe_rhs_first, within=pyo.Reals
    )
    model.noe_limit_second = pyo.Param(
        initialize=noe_rhs_second, within=pyo.Reals
    )

    model.x = pyo.Var(model.P, model.AA, domain=pyo.Binary)

    def peak_capacity_rule(instance, peak):
        return pyo.quicksum(
            instance.x[peak, amino_acid] for amino_acid in instance.AA
        ) <= 1

    model.peak_capacity = pyo.Constraint(model.P, rule=peak_capacity_rule)

    def amino_acid_capacity_rule(instance, amino_acid):
        return pyo.quicksum(
            instance.x[peak, amino_acid] for peak in instance.P
        ) <= 1

    model.amino_acid_capacity = pyo.Constraint(
        model.AA, rule=amino_acid_capacity_rule
    )

    model.assignment_total = pyo.Constraint(
        expr=pyo.quicksum(
            model.x[peak, amino_acid]
            for peak in model.P
            for amino_acid in model.AA
        ) == model.required_assignments
    )
    model.noe_first = pyo.Constraint(
        expr=model.x[1, 1] + model.x[2, 0] <= model.noe_limit_first
    )
    model.noe_second = pyo.Constraint(
        expr=model.x[1, 3] + model.x[2, 0] <= model.noe_limit_second
    )

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.cost[peak, amino_acid] * model.x[peak, amino_acid]
            for peak in model.P
            for amino_acid in model.AA
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Allow objective retrieval to determine success after this known
        # APPsi solution-loading failure; propagate unexpected exceptions.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}