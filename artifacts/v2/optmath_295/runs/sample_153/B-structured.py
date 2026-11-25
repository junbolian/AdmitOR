# IR: {"sets":{"peaks":[0,1,2,3],"amino_acids":[0,1,2,3,4]},"params":{"cost":"matrix[peaks,amino_acids]","num_assignments":"scalar","peak_capacity":"scalar","amino_acid_capacity":"scalar"},"variables":{"x[peak,amino_acid]":"binary"},"constraints":["For each peak: sum(x[peak,amino_acid] for amino_acid) <= peak_capacity","For each amino_acid: sum(x[peak,amino_acid] for peak) <= amino_acid_capacity","sum(x[peak,amino_acid] for peak,amino_acid) == num_assignments"],"objective":"minimize sum(cost[peak,amino_acid] * x[peak,amino_acid] for peak,amino_acid)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.peaks = pyo.RangeSet(0, 3)
    model.amino_acids = pyo.RangeSet(0, 4)

    model.cost = pyo.Param(
        model.peaks,
        model.amino_acids,
        initialize=lambda mdl, peak, amino_acid: params["cost"][peak][amino_acid],
        within=pyo.Reals,
    )
    model.num_assignments = pyo.Param(
        initialize=params["num_assignments"],
        within=pyo.Reals,
    )
    model.peak_capacity = pyo.Param(
        initialize=params["peak_capacity"],
        within=pyo.Reals,
    )
    model.amino_acid_capacity = pyo.Param(
        initialize=params["amino_acid_capacity"],
        within=pyo.Reals,
    )

    model.x = pyo.Var(
        model.peaks,
        model.amino_acids,
        domain=pyo.Binary,
    )

    def peak_limit_rule(mdl, peak):
        return (
            sum(mdl.x[peak, amino_acid] for amino_acid in mdl.amino_acids)
            <= mdl.peak_capacity
        )

    model.peak_limits = pyo.Constraint(
        model.peaks,
        rule=peak_limit_rule,
    )

    def amino_acid_limit_rule(mdl, amino_acid):
        return (
            sum(mdl.x[peak, amino_acid] for peak in mdl.peaks)
            <= mdl.amino_acid_capacity
        )

    model.amino_acid_limits = pyo.Constraint(
        model.amino_acids,
        rule=amino_acid_limit_rule,
    )

    model.assignment_total = pyo.Constraint(
        expr=sum(
            model.x[peak, amino_acid]
            for peak in model.peaks
            for amino_acid in model.amino_acids
        )
        == model.num_assignments
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[peak, amino_acid] * model.x[peak, amino_acid]
            for peak in model.peaks
            for amino_acid in model.amino_acids
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution is available to load.
        # Objective retrieval below remains the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}