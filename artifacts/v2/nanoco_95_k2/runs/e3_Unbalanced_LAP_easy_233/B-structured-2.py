# IR: {"sets":{"attorneys":"0..7","documents":"0..3"},"params":{"cost":{"source":"params['cost']","shape":[8,4],"type":"real"}},"variables":{"assign[a,d]":"binary"},"constraints":["For each document d: sum(assign[a,d] for a in attorneys) == 1","For each attorney a: sum(assign[a,d] for d in documents) <= 1"],"objective":"minimize sum(cost[a,d] * assign[a,d] for a in attorneys for d in documents)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]

    model = pyo.ConcreteModel()
    model.attorneys = pyo.RangeSet(0, 7)
    model.documents = pyo.RangeSet(0, 3)

    model.cost = pyo.Param(
        model.attorneys,
        model.documents,
        initialize={
            (attorney, document): cost[attorney][document]
            for attorney in model.attorneys
            for document in model.documents
        },
        within=pyo.Reals,
    )

    model.assign = pyo.Var(
        model.attorneys,
        model.documents,
        domain=pyo.Binary,
    )

    def document_assignment_rule(instance, document):
        return sum(
            instance.assign[attorney, document]
            for attorney in instance.attorneys
        ) == 1

    model.document_assignment = pyo.Constraint(
        model.documents,
        rule=document_assignment_rule,
    )

    def attorney_capacity_rule(instance, attorney):
        return sum(
            instance.assign[attorney, document]
            for document in instance.documents
        ) <= 1

    model.attorney_capacity = pyo.Constraint(
        model.attorneys,
        rule=attorney_capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[attorney, document] * model.assign[attorney, document]
            for attorney in model.attorneys
            for document in model.documents
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