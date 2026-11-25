# IR: {"sets":{"peaks":[0,1,2,3],"amino_acids":[0,1,2,3,4]},"params":{"cost":"params['cost'][i][j]"},"variables":{"x[i,j]":"binary"},"constraints":["sum_j x[i,j] <= 1 for each peak i","sum_i x[i,j] <= 1 for each amino acid j","sum_i sum_j x[i,j] == 2"],"objective":"minimize sum_i sum_j cost[i,j]*x[i,j]"}
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
        initialize=lambda mdl, i, j: cost[i][j],
        within=pyo.Reals,
    )
    model.x = pyo.Var(
        model.peaks,
        model.amino_acids,
        domain=pyo.Binary,
    )

    def peak_limit_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.amino_acids) <= 1

    model.peak_limit = pyo.Constraint(
        model.peaks, rule=peak_limit_rule
    )

    def amino_acid_limit_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.peaks) <= 1

    model.amino_acid_limit = pyo.Constraint(
        model.amino_acids, rule=amino_acid_limit_rule
    )

    model.assignment_count = pyo.Constraint(
        expr=sum(
            model.x[i, j]
            for i in model.peaks
            for j in model.amino_acids
        ) == 2
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[i, j] * model.x[i, j]
            for i in model.peaks
            for j in model.amino_acids
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