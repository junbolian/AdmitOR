# IR: {"sets":{"B":[0,1,2,3,4],"V":[0,1,2],"P":"{(i,k): i,k in B, i<k}"},"params":{"s[i,j]":"params['processing_times'][i][j], nonnegative","H":"sum(s[i,j] for i in B for j in V)"},"variables":{"start[i,j]":"continuous, 0 <= start[i,j] <= H-s[i,j]","before[i,k,j]":"binary, (i,k) in P, j in V","makespan":"continuous, 0 <= makespan <= H"},"constraints":["start[i,j+1] >= start[i,j]+s[i,j], i in B, j in {0,1}","start[k,j] >= start[i,j]+s[i,j]-H*(1-before[i,k,j]), (i,k) in P, j in V","start[i,j] >= start[k,j]+s[k,j]-H*before[i,k,j], (i,k) in P, j in V","makespan >= start[i,2]+s[i,2], i in B"],"objective":"minimize makespan"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    processing_times = params["processing_times"]
    if len(processing_times) != 5 or any(
        len(row) != 3 for row in processing_times
    ):
        raise ValueError("processing_times must be a 5x3 matrix.")

    durations = {
        (batch, vat): float(processing_times[batch][vat])
        for batch in range(5)
        for vat in range(3)
    }

    model = pyo.ConcreteModel()
    model.batches = pyo.RangeSet(0, 4)
    model.vats = pyo.RangeSet(0, 2)
    model.batch_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (first, second)
            for first in range(5)
            for second in range(first + 1, 5)
        ],
    )
    model.duration = pyo.Param(
        model.batches,
        model.vats,
        initialize=durations,
        within=pyo.NonNegativeReals,
    )

    horizon = sum(
        pyo.value(model.duration[batch, vat])
        for batch in model.batches
        for vat in model.vats
    )

    def start_bounds(instance, batch, vat):
        return 0, horizon - pyo.value(instance.duration[batch, vat])

    model.start = pyo.Var(
        model.batches,
        model.vats,
        domain=pyo.NonNegativeReals,
        bounds=start_bounds,
    )
    model.before = pyo.Var(
        model.batch_pairs,
        model.vats,
        domain=pyo.Binary,
    )
    model.makespan = pyo.Var(
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )

    def vat_sequence_rule(instance, batch, vat):
        return (
            instance.start[batch, vat + 1]
            >= instance.start[batch, vat] + instance.duration[batch, vat]
        )

    model.vat_sequence = pyo.Constraint(
        model.batches,
        range(2),
        rule=vat_sequence_rule,
    )

    def first_before_second_rule(instance, first, second, vat):
        return (
            instance.start[second, vat]
            >= instance.start[first, vat]
            + instance.duration[first, vat]
            - horizon * (1 - instance.before[first, second, vat])
        )

    model.first_before_second = pyo.Constraint(
        model.batch_pairs,
        model.vats,
        rule=first_before_second_rule,
    )

    def second_before_first_rule(instance, first, second, vat):
        return (
            instance.start[first, vat]
            >= instance.start[second, vat]
            + instance.duration[second, vat]
            - horizon * instance.before[first, second, vat]
        )

    model.second_before_first = pyo.Constraint(
        model.batch_pairs,
        model.vats,
        rule=second_before_first_rule,
    )

    def final_completion_rule(instance, batch):
        return (
            instance.makespan
            >= instance.start[batch, 2] + instance.duration[batch, 2]
        )

    model.final_completion = pyo.Constraint(
        model.batches,
        rule=final_completion_rule,
    )
    model.total_completion_time = pyo.Objective(
        expr=model.makespan,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_completion_time))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}