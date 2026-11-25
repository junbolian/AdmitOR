# IR: {"sets":{"analysts":[0,1,2,3,4],"incidents":[0,1,2,3,4]},"params":{"duration_matrix":"params['duration_matrix']; nonnegative duration[analyst][incident]"},"variables":{"assigned[a,i]":"binary","max_duration":"nonnegative real"},"constraints":["For each analyst a: sum_i assigned[a,i] = 1","For each incident i: sum_a assigned[a,i] = 1","For each (a,i): max_duration >= duration_matrix[a][i] * assigned[a,i]"],"objective":"minimize max_duration"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    duration_matrix = params["duration_matrix"]

    model = pyo.ConcreteModel()
    model.analysts = pyo.RangeSet(0, 4)
    model.incidents = pyo.RangeSet(0, 4)

    model.duration = pyo.Param(
        model.analysts,
        model.incidents,
        initialize={
            (analyst, incident): duration_matrix[analyst][incident]
            for analyst in model.analysts
            for incident in model.incidents
        },
        within=pyo.NonNegativeReals,
    )

    model.assigned = pyo.Var(
        model.analysts,
        model.incidents,
        domain=pyo.Binary,
    )
    model.max_duration = pyo.Var(domain=pyo.NonNegativeReals)

    def analyst_assignment_rule(instance, analyst):
        return sum(
            instance.assigned[analyst, incident]
            for incident in instance.incidents
        ) == 1

    model.analyst_assignment = pyo.Constraint(
        model.analysts,
        rule=analyst_assignment_rule,
    )

    def incident_assignment_rule(instance, incident):
        return sum(
            instance.assigned[analyst, incident]
            for analyst in instance.analysts
        ) == 1

    model.incident_assignment = pyo.Constraint(
        model.incidents,
        rule=incident_assignment_rule,
    )

    def bottleneck_rule(instance, analyst, incident):
        return (
            instance.max_duration
            >= instance.duration[analyst, incident]
            * instance.assigned[analyst, incident]
        )

    model.bottleneck_bound = pyo.Constraint(
        model.analysts,
        model.incidents,
        rule=bottleneck_rule,
    )

    model.objective = pyo.Objective(
        expr=model.max_duration,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}