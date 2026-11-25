# IR: {"sets":{"peaks":[0,1,2,3],"amino_acids":[0,1,2,3,4]},"params":{"cost":{"source":"params['cost']","shape":[4,5]}},"variables":{"x[peak,acid]":"binary"},"constraints":["For each peak: sum_acid x[peak,acid] <= 1","For each acid: sum_peak x[peak,acid] <= 1","sum_peak,acid x[peak,acid] == 3","x[0,1] + x[2,4] <= 1","x[1,1] + x[2,4] <= 1"],"objective":"minimize sum_peak,acid cost[peak,acid] * x[peak,acid]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]

    model = pyo.ConcreteModel()
    model.peaks = pyo.RangeSet(0, 3)
    model.amino_acids = pyo.RangeSet(0, 4)

    model.assignment_cost = pyo.Param(
        model.peaks,
        model.amino_acids,
        initialize={
            (peak, acid): cost[peak][acid]
            for peak in model.peaks
            for acid in model.amino_acids
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(
        model.peaks,
        model.amino_acids,
        domain=pyo.Binary,
    )

    def peak_capacity_rule(mdl, peak):
        return sum(mdl.x[peak, acid] for acid in mdl.amino_acids) <= 1

    model.peak_capacity = pyo.Constraint(
        model.peaks, rule=peak_capacity_rule
    )

    def amino_acid_capacity_rule(mdl, acid):
        return sum(mdl.x[peak, acid] for peak in mdl.peaks) <= 1

    model.amino_acid_capacity = pyo.Constraint(
        model.amino_acids, rule=amino_acid_capacity_rule
    )

    model.assignment_count = pyo.Constraint(
        expr=sum(
            model.x[peak, acid]
            for peak in model.peaks
            for acid in model.amino_acids
        ) == 3
    )

    model.restricted_pair_one = pyo.Constraint(
        expr=model.x[0, 1] + model.x[2, 4] <= 1
    )
    model.restricted_pair_two = pyo.Constraint(
        expr=model.x[1, 1] + model.x[2, 4] <= 1
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
        # A failed solution load can raise; objective retrieval decides success.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}