# IR: {"sets":{"P":"range(params['num_peaks'])","A":"range(params['num_amino_acids'])"},"params":{"cost":"params['cost'][peak][amino_acid]","num_assignments":"params['num_assignments']","num_peaks":"params['num_peaks'] (frozen set size)","num_amino_acids":"params['num_amino_acids'] (frozen set size)"},"variables":{"x[P,A]":"binary"},"constraints":{"peak_limit":"sum(x[peak,aa] for aa in A) <= 1 for each peak in P","amino_acid_limit":"sum(x[peak,aa] for peak in P) <= 1 for each aa in A","assignment_count":"sum(x[peak,aa] for peak in P for aa in A) == num_assignments"},"objective":"minimize sum(cost[peak,aa]*x[peak,aa] for peak in P for aa in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_peaks = params["num_peaks"]
    num_amino_acids = params["num_amino_acids"]
    num_assignments = params["num_assignments"]
    cost = params["cost"]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=range(num_peaks), ordered=True)
    model.A = pyo.Set(initialize=range(num_amino_acids), ordered=True)

    model.cost = pyo.Param(
        model.P,
        model.A,
        initialize=lambda mdl, peak, aa: cost[peak][aa],
        within=pyo.Reals,
    )
    model.num_assignments = pyo.Param(
        initialize=num_assignments,
        within=pyo.Reals,
        mutable=True,
    )

    model.x = pyo.Var(model.P, model.A, domain=pyo.Binary)

    def peak_limit_rule(mdl, peak):
        if not len(mdl.A):
            return pyo.Constraint.Feasible
        return pyo.quicksum(mdl.x[peak, aa] for aa in mdl.A) <= 1

    def amino_acid_limit_rule(mdl, aa):
        if not len(mdl.P):
            return pyo.Constraint.Feasible
        return pyo.quicksum(mdl.x[peak, aa] for peak in mdl.P) <= 1

    model.peak_limit = pyo.Constraint(model.P, rule=peak_limit_rule)
    model.amino_acid_limit = pyo.Constraint(
        model.A, rule=amino_acid_limit_rule
    )
    model.assignment_count = pyo.Constraint(
        expr=pyo.quicksum(
            model.x[peak, aa] for peak in model.P for aa in model.A
        )
        == model.num_assignments
    )

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.cost[peak, aa] * model.x[peak, aa]
            for peak in model.P
            for aa in model.A
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