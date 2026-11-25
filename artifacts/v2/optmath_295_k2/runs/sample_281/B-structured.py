# IR: {"sets":{"peaks":[0,1,2,3,4],"amino_acids":[0,1,2,3,4,5],"noe_conflicts":[[0,0,4,1],[0,0,4,3],[0,0,4,4],[1,0,2,1],[1,0,2,3],[1,0,2,4]]},"params":{"assignment_costs":"5x6 cost matrix","total_assignments_required":"exact assignment count"},"variables":{"x[p,a]":"binary"},"constraints":["sum_a x[p,a] <= 1 for each peak p","sum_p x[p,a] <= 1 for each amino acid a","sum_{p,a} x[p,a] = total_assignments_required","x[p,a] + x[q,b] <= 1 for each (p,a,q,b) in noe_conflicts"],"objective":"minimize sum_{p,a} assignment_costs[p][a]*x[p,a]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    assignment_costs = params["assignment_costs"]
    total_assignments_required = params["total_assignments_required"]

    model = pyo.ConcreteModel()
    model.peaks = pyo.RangeSet(0, 4)
    model.amino_acids = pyo.RangeSet(0, 5)

    # Only the NOE conflicts explicitly supplied in the problem are imposed.
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

    model.assignment_cost = pyo.Param(
        model.peaks,
        model.amino_acids,
        initialize={
            (peak, acid): assignment_costs[peak][acid]
            for peak in model.peaks
            for acid in model.amino_acids
        },
        within=pyo.Reals,
    )
    model.required_count = pyo.Param(
        initialize=total_assignments_required,
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.peaks, model.amino_acids, domain=pyo.Binary)

    def peak_uniqueness_rule(mod, peak):
        return sum(mod.x[peak, acid] for acid in mod.amino_acids) <= 1

    model.peak_uniqueness = pyo.Constraint(
        model.peaks, rule=peak_uniqueness_rule
    )

    def acid_uniqueness_rule(mod, acid):
        return sum(mod.x[peak, acid] for peak in mod.peaks) <= 1

    model.acid_uniqueness = pyo.Constraint(
        model.amino_acids, rule=acid_uniqueness_rule
    )

    model.assignment_count = pyo.Constraint(
        expr=sum(
            model.x[peak, acid]
            for peak in model.peaks
            for acid in model.amino_acids
        )
        == model.required_count
    )

    def noe_rule(mod, peak, acid, other_peak, other_acid):
        return mod.x[peak, acid] + mod.x[other_peak, other_acid] <= 1

    model.noe_restrictions = pyo.Constraint(
        model.noe_conflicts, rule=noe_rule
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
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}