# IR: {"sets":{"peaks":[0,1,2,3],"amino_acids":[0,1,2,3,4]},"params":{"cost_matrix":"params['cost_matrix'][i][j]"},"variables":{"assignment[i,j]":"binary"},"constraints":["For each peak i: sum_j assignment[i,j] <= 1","For each amino acid j: sum_i assignment[i,j] <= 1","sum_i sum_j assignment[i,j] == 2"],"objective":"minimize sum_i sum_j cost_matrix[i][j] * assignment[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]

    model = pyo.ConcreteModel()
    model.peaks = pyo.RangeSet(0, 3)
    model.amino_acids = pyo.RangeSet(0, 4)

    model.assignment_cost = pyo.Param(
        model.peaks,
        model.amino_acids,
        initialize=lambda mdl, i, j: cost_matrix[i][j],
        within=pyo.Reals,
    )
    model.assignment = pyo.Var(
        model.peaks,
        model.amino_acids,
        domain=pyo.Binary,
    )

    model.peak_capacity = pyo.Constraint(
        model.peaks,
        rule=lambda mdl, i: sum(
            mdl.assignment[i, j] for j in mdl.amino_acids
        ) <= 1,
    )
    model.amino_acid_capacity = pyo.Constraint(
        model.amino_acids,
        rule=lambda mdl, j: sum(
            mdl.assignment[i, j] for i in mdl.peaks
        ) <= 1,
    )
    model.assignment_count = pyo.Constraint(
        expr=sum(
            model.assignment[i, j]
            for i in model.peaks
            for j in model.amino_acids
        ) == 2,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[i, j] * model.assignment[i, j]
            for i in model.peaks
            for j in model.amino_acids
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