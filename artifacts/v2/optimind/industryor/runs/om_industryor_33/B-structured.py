# IR: {"sets":{"B":[0,1,2,3,4],"V":[0,1,2],"P":"{(i,k): i,k in B, i<k}"},"params":{"processing_times":"params['processing_times'][i][j], nonnegative finite hours","big_M":"sum(processing_times[i][j] for i in B for j in V)"},"variables":{"start[i,j]":"NonNegativeReals, i in B, j in V","before[i,k,j]":"Binary, (i,k) in P, j in V; 1 means i precedes k in vat j","makespan":"NonNegativeReals"},"constraints":["start[i,j+1] >= start[i,j] + processing_times[i,j], i in B, j in {0,1}","start[k,j] >= start[i,j] + processing_times[i,j] - big_M*(1-before[i,k,j]), (i,k) in P, j in V","start[i,j] >= start[k,j] + processing_times[k,j] - big_M*before[i,k,j], (i,k) in P, j in V","makespan >= start[i,2] + processing_times[i,2], i in B"],"objective":"minimize makespan"}

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    processing_times = params["processing_times"]

    if len(processing_times) != 5 or any(
        len(row) != 3 for row in processing_times
    ):
        return {"objective": None, "status": "invalid_dimensions"}

    durations = {
        (batch, vat): float(processing_times[batch][vat])
        for batch in range(5)
        for vat in range(3)
    }

    if any(
        not math.isfinite(duration) or duration < 0
        for duration in durations.values()
    ):
        return {"objective": None, "status": "invalid_processing_times"}

    model = pyo.ConcreteModel()

    model.B = pyo.RangeSet(0, 4)
    model.V = pyo.RangeSet(0, 2)
    model.P = pyo.Set(
        dimen=2,
        initialize=[
            (first, second)
            for first in range(5)
            for second in range(first + 1, 5)
        ],
    )

    model.processing_times = pyo.Param(
        model.B,
        model.V,
        initialize=durations,
        within=pyo.NonNegativeReals,
    )

    # A fully serial schedule finishes within this horizon, so this
    # derived bound is sufficient for an optimal schedule.
    model.big_M = pyo.Param(initialize=sum(durations.values()))

    model.start = pyo.Var(
        model.B, model.V, domain=pyo.NonNegativeReals
    )
    model.before = pyo.Var(
        model.P, model.V, domain=pyo.Binary
    )
    model.makespan = pyo.Var(domain=pyo.NonNegativeReals)

    def flow_rule(md, batch, vat):
        return (
            md.start[batch, vat + 1]
            >= md.start[batch, vat] + md.processing_times[batch, vat]
        )

    model.flow_constraints = pyo.Constraint(
        model.B, range(2), rule=flow_rule
    )

    def first_before_second_rule(md, first, second, vat):
        return (
            md.start[second, vat]
            >= md.start[first, vat]
            + md.processing_times[first, vat]
            - md.big_M * (1 - md.before[first, second, vat])
        )

    model.first_before_second_constraints = pyo.Constraint(
        model.P, model.V, rule=first_before_second_rule
    )

    def second_before_first_rule(md, first, second, vat):
        return (
            md.start[first, vat]
            >= md.start[second, vat]
            + md.processing_times[second, vat]
            - md.big_M * md.before[first, second, vat]
        )

    model.second_before_first_constraints = pyo.Constraint(
        model.P, model.V, rule=second_before_first_rule
    )

    def completion_rule(md, batch):
        return (
            md.makespan
            >= md.start[batch, 2] + md.processing_times[batch, 2]
        )

    model.completion_constraints = pyo.Constraint(
        model.B, rule=completion_rule
    )

    model.total_completion_time = pyo.Objective(
        expr=model.makespan,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_completion_time))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}