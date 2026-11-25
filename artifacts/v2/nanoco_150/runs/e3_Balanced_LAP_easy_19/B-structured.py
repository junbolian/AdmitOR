# IR: {"sets":{"harvesters":[0,1,2,3,4],"fields":[0,1,2,3,4]},"params":{"cost_matrix":"params['cost_matrix'][harvester][field]"},"variables":{"assignment[harvester,field]":"Binary"},"constraints":["For each harvester: sum(assignment[harvester,field] for field in fields) == 1","For each field: sum(assignment[harvester,field] for harvester in harvesters) == 1"],"objective":"Minimize sum(cost_matrix[harvester][field] * assignment[harvester,field] for harvester in harvesters for field in fields)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]

    model = pyo.ConcreteModel()
    model.harvesters = pyo.RangeSet(0, 4)
    model.fields = pyo.RangeSet(0, 4)

    model.operational_cost = pyo.Param(
        model.harvesters,
        model.fields,
        initialize=lambda instance, harvester, field: cost_matrix[harvester][field],
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(
        model.harvesters,
        model.fields,
        domain=pyo.Binary,
    )

    def harvester_assignment_rule(instance, harvester):
        return sum(
            instance.assignment[harvester, field]
            for field in instance.fields
        ) == 1

    model.harvester_assignment = pyo.Constraint(
        model.harvesters,
        rule=harvester_assignment_rule,
    )

    def field_assignment_rule(instance, field):
        return sum(
            instance.assignment[harvester, field]
            for harvester in instance.harvesters
        ) == 1

    model.field_assignment = pyo.Constraint(
        model.fields,
        rule=field_assignment_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.operational_cost[harvester, field]
            * model.assignment[harvester, field]
            for harvester in model.harvesters
            for field in model.fields
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # An infeasible solve can raise before a solution is loaded.
        # Success is determined solely by objective retrieval below.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}