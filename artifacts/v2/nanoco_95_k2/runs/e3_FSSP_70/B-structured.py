# IR: {"sets":{"J":"range(num_jobs)","S":"range(num_stations)","P":"{(j,k): j,k in J and j<k}"},"params":{"processing_times":"params['processing_times']; finite nonnegative matrix indexed by J,S","num_jobs":"params['num_jobs']; positive integer","num_stations":"params['num_stations']; positive integer","H":"sum(processing_times[j][s] for j in J for s in S)"},"variables":{"start[j,s]":"continuous in [0,H]","end[j,s]":"continuous in [0,H]","before[j,k,s]":"binary for (j,k) in P,s in S","makespan":"continuous in [0,H]"},"constraints":["end[j,s] = start[j,s] + processing_times[j][s] for j in J,s in S","start[j,s+1] = end[j,s] for j in J,s in S except the last station (immediate transfer)","end[j,s] <= start[k,s] + H*(1-before[j,k,s]) for (j,k) in P,s in S","end[k,s] <= start[j,s] + H*before[j,k,s] for (j,k) in P,s in S","makespan >= end[j,num_stations-1] for j in J"],"objective":"minimize makespan"}
import math
import operator

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    processing_times = params["processing_times"]
    num_jobs = operator.index(params["num_jobs"])
    num_stations = operator.index(params["num_stations"])

    if num_jobs <= 0 or num_stations <= 0:
        raise ValueError("num_jobs and num_stations must be positive integers.")

    if len(processing_times) != num_jobs:
        raise ValueError("processing_times must contain one row per job.")

    durations = {}
    for job in range(num_jobs):
        if len(processing_times[job]) != num_stations:
            raise ValueError(
                "Each processing_times row must contain one value per station."
            )
        for station in range(num_stations):
            duration = float(processing_times[job][station])
            if not math.isfinite(duration) or duration < 0:
                raise ValueError(
                    "Processing times must be finite and nonnegative."
                )
            durations[job, station] = duration

    # Processing whole jobs consecutively gives a feasible no-wait schedule
    # within this horizon, so it is also a valid disjunction constant.
    horizon = sum(durations.values())
    if not math.isfinite(horizon):
        raise ValueError("The total processing time must be finite.")

    model = pyo.ConcreteModel()
    model.job_set = pyo.Set(initialize=range(num_jobs), ordered=True)
    model.station_set = pyo.Set(initialize=range(num_stations), ordered=True)
    model.pair_set = pyo.Set(
        dimen=2,
        initialize=[
            (first_job, second_job)
            for first_job in range(num_jobs)
            for second_job in range(first_job + 1, num_jobs)
        ],
    )
    model.duration = pyo.Param(
        model.job_set,
        model.station_set,
        initialize=durations,
        within=pyo.NonNegativeReals,
    )

    model.start = pyo.Var(
        model.job_set, model.station_set, bounds=(0, horizon)
    )
    model.end = pyo.Var(
        model.job_set, model.station_set, bounds=(0, horizon)
    )
    model.before = pyo.Var(
        model.pair_set, model.station_set, domain=pyo.Binary
    )
    model.makespan = pyo.Var(bounds=(0, horizon))

    def duration_rule(instance, job, station):
        return (
            instance.end[job, station]
            == instance.start[job, station] + instance.duration[job, station]
        )

    model.operation_duration = pyo.Constraint(
        model.job_set, model.station_set, rule=duration_rule
    )

    def transfer_rule(instance, job, station):
        if station == num_stations - 1:
            return pyo.Constraint.Skip
        return instance.start[job, station + 1] == instance.end[job, station]

    model.immediate_transfer = pyo.Constraint(
        model.job_set, model.station_set, rule=transfer_rule
    )

    def first_precedes_rule(instance, first_job, second_job, station):
        return instance.end[first_job, station] <= (
            instance.start[second_job, station]
            + horizon * (1 - instance.before[first_job, second_job, station])
        )

    model.first_precedes = pyo.Constraint(
        model.pair_set, model.station_set, rule=first_precedes_rule
    )

    def second_precedes_rule(instance, first_job, second_job, station):
        return instance.end[second_job, station] <= (
            instance.start[first_job, station]
            + horizon * instance.before[first_job, second_job, station]
        )

    model.second_precedes = pyo.Constraint(
        model.pair_set, model.station_set, rule=second_precedes_rule
    )

    def completion_rule(instance, job):
        return instance.makespan >= instance.end[job, num_stations - 1]

    model.workflow_completion = pyo.Constraint(
        model.job_set, rule=completion_rule
    )
    model.makespan_objective = pyo.Objective(
        expr=model.makespan, sense=pyo.minimize
    )

    solver_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        # Appsi can raise when it cannot load a feasible solution.
        # Objective retrieval below remains the sole success criterion.
        solver_failed = True

    try:
        obj_val = float(pyo.value(model.makespan_objective))
    except ValueError:
        return {
            "objective": None,
            "status": "solve_failed" if solver_failed else "objective_unavailable",
        }

    return {"objective": obj_val, "status": "optimal"}