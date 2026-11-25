# IR: {"sets":{"B":"range(num_batches)","S":"range(num_stations)","P":"{(i,j): i,j in B, i<j}"},"params":{"processing_times":"nonnegative flat batch-major array","num_stations":"positive integer","num_batches":"positive integer","p[b,s]":"processing_times[b*num_stations+s]","H":"sum(processing_times)"},"variables":{"start[b,s]":"continuous [0,H]","finish[b,s]":"continuous [0,H]","before[i,j,s]":"binary for (i,j) in P","makespan":"continuous [0,H]"},"constraints":["finish[b,s] = start[b,s] + p[b,s]","start[b,1] = finish[b,0] when num_stations >= 2 (immediate transfer to Station 1)","start[b,s+1] >= finish[b,s] for s >= 1 and s+1 < num_stations","start[j,s] >= finish[i,s] - H*(1-before[i,j,s]) for (i,j) in P","start[i,s] >= finish[j,s] - H*before[i,j,s] for (i,j) in P","makespan >= finish[b,num_stations-1]"],"objective":"minimize makespan"}

import math

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_stations = params["num_stations"]
    num_batches = params["num_batches"]
    processing_times = params["processing_times"]

    if (
        isinstance(num_stations, bool)
        or isinstance(num_batches, bool)
        or not isinstance(num_stations, int)
        or not isinstance(num_batches, int)
        or num_stations <= 0
        or num_batches <= 0
    ):
        return {"objective": None, "status": "invalid_dimensions"}

    if len(processing_times) != num_batches * num_stations:
        return {"objective": None, "status": "invalid_processing_times"}

    durations = {
        (batch, station): float(
            processing_times[batch * num_stations + station]
        )
        for batch in range(num_batches)
        for station in range(num_stations)
    }

    if any(
        not math.isfinite(duration) or duration < 0
        for duration in durations.values()
    ):
        return {"objective": None, "status": "invalid_processing_times"}

    horizon = sum(durations.values())
    if not math.isfinite(horizon):
        return {"objective": None, "status": "invalid_horizon"}

    model = pyo.ConcreteModel()

    model.batches = pyo.RangeSet(0, num_batches - 1)
    model.stations = pyo.RangeSet(0, num_stations - 1)
    model.batch_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (first_batch, second_batch)
            for first_batch in range(num_batches)
            for second_batch in range(first_batch + 1, num_batches)
        ],
    )

    model.duration = pyo.Param(
        model.batches,
        model.stations,
        initialize=durations,
        within=pyo.NonNegativeReals,
    )
    model.horizon = pyo.Param(
        initialize=horizon,
        within=pyo.NonNegativeReals,
    )

    model.start = pyo.Var(
        model.batches,
        model.stations,
        within=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )
    model.finish = pyo.Var(
        model.batches,
        model.stations,
        within=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )
    model.before = pyo.Var(
        model.batch_pairs,
        model.stations,
        within=pyo.Binary,
    )
    model.makespan = pyo.Var(
        within=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )

    def duration_rule(model, batch, station):
        return (
            model.finish[batch, station]
            == model.start[batch, station] + model.duration[batch, station]
        )

    model.operation_duration = pyo.Constraint(
        model.batches,
        model.stations,
        rule=duration_rule,
    )

    def sequence_rule(model, batch, station):
        if station == num_stations - 1:
            return pyo.Constraint.Skip
        if station == 0:
            return model.start[batch, station + 1] == model.finish[batch, station]
        return model.start[batch, station + 1] >= model.finish[batch, station]

    model.stage_sequence = pyo.Constraint(
        model.batches,
        model.stations,
        rule=sequence_rule,
    )

    def first_before_second_rule(model, first_batch, second_batch, station):
        return (
            model.start[second_batch, station]
            >= model.finish[first_batch, station]
            - model.horizon * (1 - model.before[first_batch, second_batch, station])
        )

    model.first_before_second = pyo.Constraint(
        model.batch_pairs,
        model.stations,
        rule=first_before_second_rule,
    )

    def second_before_first_rule(model, first_batch, second_batch, station):
        return (
            model.start[first_batch, station]
            >= model.finish[second_batch, station]
            - model.horizon * model.before[first_batch, second_batch, station]
        )

    model.second_before_first = pyo.Constraint(
        model.batch_pairs,
        model.stations,
        rule=second_before_first_rule,
    )

    def makespan_rule(model, batch):
        return model.makespan >= model.finish[batch, num_stations - 1]

    model.completion_bound = pyo.Constraint(
        model.batches,
        rule=makespan_rule,
    )
    model.total_cycle_time = pyo.Objective(
        expr=model.makespan,
        sense=pyo.minimize,
    )

    solve_failed = False
    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        solve_failed = True

    # Success is determined exclusively by objective-value retrieval.
    try:
        obj_val = float(pyo.value(model.total_cycle_time))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": "solve_failed" if solve_failed else "no_objective",
        }

    return {"objective": obj_val, "status": "optimal"}