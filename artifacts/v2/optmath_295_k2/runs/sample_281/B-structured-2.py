# IR: {"sets":{"peaks":[0,1,2,3,4],"amino_acids":[0,1,2,3,4,5],"noe_conflicts":[[0,0,4,1],[0,0,4,3],[0,0,4,4],[1,0,2,1],[1,0,2,3],[1,0,2,4]]},"params":{"assignment_costs":"5x6 cost matrix","total_assignments_required":"exact assignment count"},"variables":{"x[p,a]":"binary"},"constraints":["For each peak p: sum_a x[p,a] <= 1","For each amino acid a: sum_p x[p,a] <= 1","sum_{p,a} x[p,a] = total_assignments_required","For each (p,a,q,b) in noe_conflicts: x[p,a] + x[q,b] <= 1"],"objective":"minimize sum_{p,a} assignment_costs[p][a] * x[p,a]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    assignment_costs = params["assignment_costs"]
    total_assignments_required = params["total_assignments_required"]

    model = pyo.ConcreteModel()
    model.peaks = pyo.RangeSet(0, 4)
    model.amino_acids = pyo.RangeSet(0, 5)

    # Only the NOE conflicts explicitly specified in the problem are included.
    model.noe_conflicts = pyo.Set(
        dimen=4,
        initialize=[
            (0, 0, 4, 1),
            (0, 0, 4, 3),
            (0, 0, 4, 4),
            (1, 0, 2, 1),
            (1, 0, 2, 3),
            (1, 0, 2, 4),
        ],
    )

    model.cost = pyo.Param(
        model.peaks,
        model.amino_acids,
        initialize=lambda mdl, peak, amino: assignment_costs[peak][amino],
        within=pyo.Reals,
    )
    model.required_count = pyo.Param(
        initialize=total_assignments_required,
        within=pyo.Reals,
    )
    model.x = pyo.Var(
        model.peaks,
        model.amino_acids,
        domain=pyo.Binary,
    )

    def peak_rule(mdl, peak):
        return sum(mdl.x[peak, amino] for amino in mdl.amino_acids) <= 1

    model.peak_uniqueness = pyo.Constraint(model.peaks, rule=peak_rule)

    def amino_rule(mdl, amino):
        return sum(mdl.x[peak, amino] for peak in mdl.peaks) <= 1

    model.amino_uniqueness = pyo.Constraint(model.amino_acids, rule=amino_rule)

    model.assignment_count = pyo.Constraint(
        expr=sum(
            model.x[peak, amino]
            for peak in model.peaks
            for amino in model.amino_acids
        )
        == model.required_count
    )

    def noe_rule(mdl, peak, amino, other_peak, other_amino):
        return mdl.x[peak, amino] + mdl.x[other_peak, other_amino] <= 1

    model.noe_restrictions = pyo.Constraint(model.noe_conflicts, rule=noe_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[peak, amino] * model.x[peak, amino]
            for peak in model.peaks
            for amino in model.amino_acids
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}