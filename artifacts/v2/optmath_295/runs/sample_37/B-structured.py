# IR: {"sets":{"peaks":[0,1,2,3],"amino_acids":[0,1,2,3,4]},"params":{"cost_matrix":"assignment costs, indexed by peak and amino acid","n_assignments":"required total assignments"},"variables":{"x[peak,aa]":"binary"},"constraints":["For each peak: sum_aa x[peak,aa] <= 1","For each aa: sum_peak x[peak,aa] <= 1","sum_peak,aa x[peak,aa] = n_assignments","x[0,1] + x[2,4] <= 1","x[1,1] + x[2,4] <= 1"],"objective":"minimize sum_peak,aa cost_matrix[peak][aa] * x[peak,aa]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    n_assignments = params["n_assignments"]

    model = pyo.ConcreteModel()

    model.peaks = pyo.RangeSet(0, 3)
    model.amino_acids = pyo.RangeSet(0, 4)

    model.assignment_cost = pyo.Param(
        model.peaks,
        model.amino_acids,
        initialize={
            (peak, aa): cost_matrix[peak][aa]
            for peak in model.peaks
            for aa in model.amino_acids
        },
        within=pyo.Reals,
    )
    model.required_assignments = pyo.Param(
        initialize=n_assignments,
        within=pyo.Reals,
    )

    model.x = pyo.Var(
        model.peaks,
        model.amino_acids,
        domain=pyo.Binary,
    )

    def peak_capacity_rule(instance, peak):
        return sum(
            instance.x[peak, aa] for aa in instance.amino_acids
        ) <= 1

    model.peak_capacity = pyo.Constraint(
        model.peaks,
        rule=peak_capacity_rule,
    )

    def amino_acid_capacity_rule(instance, aa):
        return sum(
            instance.x[peak, aa] for peak in instance.peaks
        ) <= 1

    model.amino_acid_capacity = pyo.Constraint(
        model.amino_acids,
        rule=amino_acid_capacity_rule,
    )

    model.assignment_count = pyo.Constraint(
        expr=sum(
            model.x[peak, aa]
            for peak in model.peaks
            for aa in model.amino_acids
        ) == model.required_assignments
    )

    model.restricted_pair_first = pyo.Constraint(
        expr=model.x[0, 1] + model.x[2, 4] <= 1
    )
    model.restricted_pair_second = pyo.Constraint(
        expr=model.x[1, 1] + model.x[2, 4] <= 1
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[peak, aa] * model.x[peak, aa]
            for peak in model.peaks
            for aa in model.amino_acids
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}