# IR: {"sets":{"peaks":[0,1,2,3],"amino_acids":[0,1,2,3,4]},"params":{"cost":{"source":"params['cost']","indices":["peaks","amino_acids"]}},"variables":{"x":{"indices":["peaks","amino_acids"],"type":"binary"}},"constraints":["For each peak i: sum_j x[i,j] <= 1","For each amino acid j: sum_i x[i,j] <= 1","sum_i sum_j x[i,j] == 2"],"objective":{"sense":"minimize","expression":"sum_i sum_j cost[i,j]*x[i,j]"}}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
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
            (i, j): cost[i][j]
            for i in model.peaks
            for j in model.amino_acids
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(
        model.peaks,
        model.amino_acids,
        domain=pyo.Binary,
    )

    def peak_capacity_rule(instance, i):
        return sum(instance.x[i, j] for j in instance.amino_acids) <= 1

    model.peak_capacity = pyo.Constraint(
        model.peaks, rule=peak_capacity_rule
    )

    def amino_acid_capacity_rule(instance, j):
        return sum(instance.x[i, j] for i in instance.peaks) <= 1

    model.amino_acid_capacity = pyo.Constraint(
        model.amino_acids, rule=amino_acid_capacity_rule
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
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}