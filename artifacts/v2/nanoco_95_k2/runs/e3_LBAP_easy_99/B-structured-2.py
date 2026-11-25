# IR: {"sets":{"analysts":[0,1,2,3,4],"incidents":[0,1,2,3,4]},"params":{"cost_matrix":{"source":"params[\"cost_matrix\"]","domain":"nonnegative real","indices":["analysts","incidents"]}},"variables":{"assignment":{"type":"binary","indices":["analysts","incidents"]},"makespan":{"type":"nonnegative real"}},"constraints":["For each analyst a: sum(assignment[a,i] for i in incidents) = 1","For each incident i: sum(assignment[a,i] for a in analysts) = 1","For every pair (a,i): makespan >= cost_matrix[a,i] * assignment[a,i]"],"objective":{"sense":"minimize","expression":"makespan"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]

    model = pyo.ConcreteModel()
    model.analysts = pyo.RangeSet(0, 4)
    model.incidents = pyo.RangeSet(0, 4)

    model.mitigation_duration = pyo.Param(
        model.analysts,
        model.incidents,
        initialize={
            (analyst, incident): cost_matrix[analyst][incident]
            for analyst in model.analysts
            for incident in model.incidents
        },
        within=pyo.NonNegativeReals,
    )

    model.assignment = pyo.Var(
        model.analysts,
        model.incidents,
        domain=pyo.Binary,
    )
    model.makespan = pyo.Var(domain=pyo.NonNegativeReals)

    def analyst_assignment_rule(mdl, analyst):
        return sum(
            mdl.assignment[analyst, incident]
            for incident in mdl.incidents
        ) == 1

    model.analyst_assignment_constraint = pyo.Constraint(
        model.analysts,
        rule=analyst_assignment_rule,
    )

    def incident_assignment_rule(mdl, incident):
        return sum(
            mdl.assignment[analyst, incident]
            for analyst in mdl.analysts
        ) == 1

    model.incident_assignment_constraint = pyo.Constraint(
        model.incidents,
        rule=incident_assignment_rule,
    )

    def bottleneck_rule(mdl, analyst, incident):
        return mdl.makespan >= (
            mdl.mitigation_duration[analyst, incident]
            * mdl.assignment[analyst, incident]
        )

    model.bottleneck_constraint = pyo.Constraint(
        model.analysts,
        model.incidents,
        rule=bottleneck_rule,
    )

    model.bottleneck_objective = pyo.Objective(
        expr=model.makespan,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.bottleneck_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}