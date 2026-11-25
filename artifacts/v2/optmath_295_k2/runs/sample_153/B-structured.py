# IR: {"sets":{"P":"range(params['num_peaks'])","A":"range(params['num_amino_acids'])"},"params":{"cost":"params['cost'][i][j] for i in P, j in A","num_assignments":"params['num_assignments']","num_peaks":"params['num_peaks']","num_amino_acids":"params['num_amino_acids']"},"variables":{"x[i,j]":"Binary for i in P, j in A"},"constraints":["sum(x[i,j] for j in A) <= 1 for each i in P","sum(x[i,j] for i in P) <= 1 for each j in A","sum(x[i,j] for i in P, j in A) == num_assignments"],"objective":"minimize sum(cost[i,j]*x[i,j] for i in P, j in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_peaks = params["num_peaks"]
    num_amino_acids = params["num_amino_acids"]
    num_assignments = params["num_assignments"]
    cost = params["cost"]

    model = pyo.ConcreteModel()

    model.peaks = pyo.Set(initialize=range(num_peaks), ordered=True)
    model.amino_acids = pyo.Set(
        initialize=range(num_amino_acids), ordered=True
    )

    model.assignment_cost = pyo.Param(
        model.peaks,
        model.amino_acids,
        initialize=lambda instance, i, j: cost[i][j],
        within=pyo.Reals,
    )
    model.required_assignments = pyo.Param(initialize=num_assignments)

    model.x = pyo.Var(
        model.peaks,
        model.amino_acids,
        domain=pyo.Binary,
    )

    def peak_capacity_rule(instance, i):
        return sum(
            instance.x[i, j] for j in instance.amino_acids
        ) <= 1

    model.peak_capacity = pyo.Constraint(
        model.peaks, rule=peak_capacity_rule
    )

    def amino_acid_capacity_rule(instance, j):
        return sum(
            instance.x[i, j] for i in instance.peaks
        ) <= 1

    model.amino_acid_capacity = pyo.Constraint(
        model.amino_acids, rule=amino_acid_capacity_rule
    )

    model.assignment_count = pyo.Constraint(
        expr=sum(
            model.x[i, j]
            for i in model.peaks
            for j in model.amino_acids
        ) == model.required_assignments
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
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}