# IR: {"sets":{"analysts":[0,1,2,3,4],"incidents":[0,1,2,3,4]},"params":{"cost_matrix":{"source":"params['cost_matrix']","indices":["analysts","incidents"],"domain":"NonNegativeReals"}},"variables":{"assignment":{"indices":["analysts","incidents"],"type":"Binary"},"max_duration":{"type":"NonNegativeReals"}},"constraints":["For each analyst i: sum_j assignment[i,j] = 1","For each incident j: sum_i assignment[i,j] = 1","For each (i,j): max_duration >= cost_matrix[i,j] * assignment[i,j]"],"objective":{"sense":"minimize","expression":"max_duration"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.analysts = pyo.RangeSet(0, 4)
    model.incidents = pyo.RangeSet(0, 4)

    model.cost_matrix = pyo.Param(
        model.analysts,
        model.incidents,
        initialize=lambda mdl, i, j: params["cost_matrix"][i][j],
        within=pyo.NonNegativeReals,
    )

    model.assignment = pyo.Var(
        model.analysts,
        model.incidents,
        domain=pyo.Binary,
    )
    model.max_duration = pyo.Var(domain=pyo.NonNegativeReals)

    def analyst_assignment_rule(mdl, i):
        return sum(mdl.assignment[i, j] for j in mdl.incidents) == 1

    model.analyst_assignment = pyo.Constraint(
        model.analysts,
        rule=analyst_assignment_rule,
    )

    def incident_assignment_rule(mdl, j):
        return sum(mdl.assignment[i, j] for i in mdl.analysts) == 1

    model.incident_assignment = pyo.Constraint(
        model.incidents,
        rule=incident_assignment_rule,
    )

    def bottleneck_rule(mdl, i, j):
        return (
            mdl.max_duration
            >= mdl.cost_matrix[i, j] * mdl.assignment[i, j]
        )

    model.bottleneck = pyo.Constraint(
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
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}