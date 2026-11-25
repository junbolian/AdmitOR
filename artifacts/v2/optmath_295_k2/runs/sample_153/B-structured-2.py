# IR: {"sets":{"P":"range(params['num_peaks'])","A":"range(params['num_amino_acids'])"},"params":{"cost":"params['cost'][p][a]","num_assignments":"params['num_assignments']","num_peaks":"params['num_peaks']","num_amino_acids":"params['num_amino_acids']"},"variables":{"x[p,a]":"binary for p in P, a in A"},"constraints":["sum(x[p,a] for a in A) <= 1 for each p in P","sum(x[p,a] for p in P) <= 1 for each a in A","sum(x[p,a] for p in P, a in A) == num_assignments"],"objective":"minimize sum(cost[p,a]*x[p,a] for p in P, a in A)"}

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
        initialize=lambda instance, peak, amino: cost[peak][amino],
        within=pyo.Reals,
    )
    model.required_assignments = pyo.Param(
        initialize=num_assignments,
        within=pyo.Reals,
    )

    model.x = pyo.Var(
        model.peaks,
        model.amino_acids,
        domain=pyo.Binary,
    )

    def peak_limit_rule(instance, peak):
        return (
            pyo.quicksum(
                instance.x[peak, amino] for amino in instance.amino_acids
            )
            <= 1
        )

    model.peak_limits = pyo.Constraint(
        model.peaks, rule=peak_limit_rule
    )

    def amino_limit_rule(instance, amino):
        return (
            pyo.quicksum(
                instance.x[peak, amino] for peak in instance.peaks
            )
            <= 1
        )

    model.amino_limits = pyo.Constraint(
        model.amino_acids, rule=amino_limit_rule
    )

    model.assignment_count = pyo.Constraint(
        expr=pyo.quicksum(
            model.x[peak, amino]
            for peak in model.peaks
            for amino in model.amino_acids
        )
        == model.required_assignments
    )

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.assignment_cost[peak, amino] * model.x[peak, amino]
            for peak in model.peaks
            for amino in model.amino_acids
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution can be loaded.
        # Determine success solely through objective retrieval below.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}