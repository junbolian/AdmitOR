# IR: {"sets":{"A":"attorneys 0..7","D":"documents 0..3"},"params":{"cost_matrix":"input params['cost_matrix'], indexed by attorney and document"},"variables":{"x[a,d]":"binary for a in A, d in D"},"constraints":["sum(x[a,d] for a in A) == 1 for each d in D","sum(x[a,d] for d in D) <= 1 for each a in A"],"objective":"minimize sum(cost_matrix[a][d] * x[a,d] for a in A, d in D)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]

    model = pyo.ConcreteModel()
    model.attorneys = pyo.RangeSet(0, 7)
    model.documents = pyo.RangeSet(0, 3)

    model.review_cost = pyo.Param(
        model.attorneys,
        model.documents,
        initialize=lambda mdl, attorney, document: cost_matrix[attorney][document],
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(
        model.attorneys,
        model.documents,
        domain=pyo.Binary,
    )

    def document_coverage_rule(mdl, document):
        return sum(
            mdl.assignment[attorney, document]
            for attorney in mdl.attorneys
        ) == 1

    model.document_coverage = pyo.Constraint(
        model.documents,
        rule=document_coverage_rule,
    )

    def attorney_capacity_rule(mdl, attorney):
        return sum(
            mdl.assignment[attorney, document]
            for document in mdl.documents
        ) <= 1

    model.attorney_capacity = pyo.Constraint(
        model.attorneys,
        rule=attorney_capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.review_cost[attorney, document]
            * model.assignment[attorney, document]
            for attorney in model.attorneys
            for document in model.documents
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