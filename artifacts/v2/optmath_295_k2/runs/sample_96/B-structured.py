# IR: {"sets":{"P":"range(params['peak_count'])","A":"range(params['amino_acid_count'])"},"params":["assignment_cost[P,A]","noe_rhs_peak1_aa1_peak2_aa0","noe_rhs_peak1_aa3_peak2_aa0","num_assignments","peak_count","amino_acid_count"],"decision_variables":{"x[P,A]":"binary"},"constraints":["For each p in P: sum(x[p,a] for a in A) <= 1","For each a in A: sum(x[p,a] for p in P) <= 1","sum(x[p,a] for p in P for a in A) == num_assignments","x[1,1] + x[2,0] <= noe_rhs_peak1_aa1_peak2_aa0","x[1,3] + x[2,0] <= noe_rhs_peak1_aa3_peak2_aa0"],"objective":"minimize sum(assignment_cost[p,a] * x[p,a] for p in P for a in A)","input_contract":"A complete assignment_cost matrix is required; missing parameters return failure without inventing numeric data."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # The prose does not determine every cost. A missing cost matrix cannot
    # be reconstructed exactly from the listed entries and row bounds.
    try:
        assignment_cost = params["assignment_cost"]
        peak_count = params["peak_count"]
        amino_acid_count = params["amino_acid_count"]
        num_assignments = params["num_assignments"]
        noe_rhs_first = params["noe_rhs_peak1_aa1_peak2_aa0"]
        noe_rhs_second = params["noe_rhs_peak1_aa3_peak2_aa0"]
    except KeyError as exc:
        return {
            "objective": None,
            "status": "missing_parameter:" + str(exc.args[0]),
        }

    # Accept either a nested matrix or a mapping keyed by (peak, amino).
    def get_cost(peak, amino):
        if isinstance(assignment_cost, dict) and (
            peak, amino
        ) in assignment_cost:
            return assignment_cost[peak, amino]
        return assignment_cost[peak][amino]

    try:
        costs = {
            (peak, amino): get_cost(peak, amino)
            for peak in range(peak_count)
            for amino in range(amino_acid_count)
        }
    except (KeyError, IndexError):
        return {"objective": None, "status": "incomplete_assignment_cost"}

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=range(peak_count), ordered=True)
    model.A = pyo.Set(initialize=range(amino_acid_count), ordered=True)

    model.assignment_cost = pyo.Param(
        model.P, model.A, initialize=costs, within=pyo.Reals
    )
    model.num_assignments = pyo.Param(
        initialize=num_assignments, within=pyo.Reals
    )
    model.noe_rhs_first = pyo.Param(
        initialize=noe_rhs_first, within=pyo.Reals
    )
    model.noe_rhs_second = pyo.Param(
        initialize=noe_rhs_second, within=pyo.Reals
    )

    model.x = pyo.Var(model.P, model.A, domain=pyo.Binary)

    def peak_capacity_rule(mdl, peak):
        return sum(mdl.x[peak, amino] for amino in mdl.A) <= 1

    def amino_capacity_rule(mdl, amino):
        return sum(mdl.x[peak, amino] for peak in mdl.P) <= 1

    model.peak_capacity = pyo.Constraint(
        model.P, rule=peak_capacity_rule
    )
    model.amino_capacity = pyo.Constraint(
        model.A, rule=amino_capacity_rule
    )
    model.assignment_total = pyo.Constraint(
        expr=sum(
            model.x[peak, amino]
            for peak in model.P
            for amino in model.A
        ) == model.num_assignments
    )
    model.noe_first = pyo.Constraint(
        expr=model.x[1, 1] + model.x[2, 0] <= model.noe_rhs_first
    )
    model.noe_second = pyo.Constraint(
        expr=model.x[1, 3] + model.x[2, 0] <= model.noe_rhs_second
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[peak, amino] * model.x[peak, amino]
            for peak in model.P
            for amino in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # A failed solution load can raise; objective retrieval alone
        # determines whether this function reports success.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}