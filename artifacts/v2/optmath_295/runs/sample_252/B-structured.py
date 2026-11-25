# IR: {"sets":{"P":"range(params['peak_count'])","A":"range(params['amino_acid_count'])","R":"params['noe_pairs'] (4-tuples)"},"params":{"peak_count":"frozen index-set size","amino_acid_count":"frozen index-set size","required_assignments":"exact assignment count","cost_matrix":"assignment costs","noe_pairs":"forbidden simultaneous assignment pairs"},"variables":{"x[p,a]":"binary, p in P, a in A"},"constraints":["sum(x[p,a] for a in A) <= 1 for each p in P","sum(x[p,a] for p in P) <= 1 for each a in A","sum(x[p,a] for p in P for a in A) == required_assignments","x[p,a] + x[q,b] <= 1 for each (p,a,q,b) in R"],"objective":"minimize sum(cost_matrix[p][a] * x[p,a] for p in P for a in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    peak_count = params["peak_count"]
    amino_acid_count = params["amino_acid_count"]
    required_assignments = params["required_assignments"]
    cost_matrix = params["cost_matrix"]
    noe_pairs = params["noe_pairs"]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=range(peak_count), ordered=True)
    model.A = pyo.Set(initialize=range(amino_acid_count), ordered=True)
    model.R = pyo.Set(
        dimen=4,
        initialize=[tuple(pair) for pair in noe_pairs],
        within=model.P * model.A * model.P * model.A,
    )

    model.assignment_cost = pyo.Param(
        model.P,
        model.A,
        initialize=lambda mdl, peak, amino: cost_matrix[peak][amino],
        within=pyo.Reals,
    )
    model.assignment_target = pyo.Param(
        initialize=required_assignments,
        within=pyo.NonNegativeIntegers,
    )

    model.x = pyo.Var(model.P, model.A, domain=pyo.Binary)

    def peak_capacity_rule(mdl, peak):
        return sum(mdl.x[peak, amino] for amino in mdl.A) <= 1

    model.peak_capacity = pyo.Constraint(model.P, rule=peak_capacity_rule)

    def amino_capacity_rule(mdl, amino):
        return sum(mdl.x[peak, amino] for peak in mdl.P) <= 1

    model.amino_capacity = pyo.Constraint(model.A, rule=amino_capacity_rule)

    model.exact_assignments = pyo.Constraint(
        expr=sum(
            model.x[peak, amino]
            for peak in model.P
            for amino in model.A
        ) == model.assignment_target
    )

    def noe_restriction_rule(mdl, peak_a, amino_a, peak_b, amino_b):
        return mdl.x[peak_a, amino_a] + mdl.x[peak_b, amino_b] <= 1

    model.noe_restrictions = pyo.Constraint(
        model.R,
        rule=noe_restriction_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[peak, amino] * model.x[peak, amino]
            for peak in model.P
            for amino in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # An infeasible solve may raise before a solution can be loaded.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}