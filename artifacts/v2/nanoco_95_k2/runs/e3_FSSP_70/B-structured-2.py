# IR: {"sets":{"J":"range(params['num_jobs'])","S":"range(params['num_stations'])","P":"{(i,j) in J x J: i<j}"},"params":{"processing_times":"params['processing_times'][j][s] >= 0","num_jobs":"params['num_jobs'], positive integer","num_stations":"params['num_stations'], positive integer","H":"sum(processing_times[j][s] for j in J for s in S)"},"variables":{"start[j,s]":"continuous in [0,H]","finish[j,s]":"continuous in [0,H]","precedes[i,j,s]":"binary for (i,j) in P, s in S; 1 means i precedes j","makespan":"continuous in [0,H]"},"constraints":["finish[j,s] = start[j,s] + processing_times[j][s] for j in J, s in S","start[j,s+1] = finish[j,s] for j in J, s in S except last (immediate transfer, no waiting)","finish[i,s] <= start[j,s] + H*(1-precedes[i,j,s]) for (i,j) in P, s in S","finish[j,s] <= start[i,s] + H*precedes[i,j,s] for (i,j) in P, s in S","makespan >= finish[j,num_stations-1] for j in J"],"objective":"minimize makespan"}
import math
from numbers import Integral

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_jobs = params["num_jobs"]
    num_stations = params["num_stations"]
    processing_times = params["processing_times"]

    if (
        isinstance(num_jobs, bool)
        or not isinstance(num_jobs, Integral)
        or num_jobs <= 0
        or isinstance(num_stations, bool)
        or not isinstance(num_stations, Integral)
        or num_stations <= 0
    ):
        return {"objective": None, "status": "invalid_dimensions"}

    if len(processing_times) != num_jobs or any(
        len(row) != num_stations for row in processing_times
    ):
        return {"objective": None, "status": "invalid_dimensions"}

    durations = {
        (job, station): float(processing_times[job][station])
        for job in range(num_jobs)
        for station in range(num_stations)
    }
    if any(
        not math.isfinite(duration) or duration < 0
        for duration in durations.values()
    ):
        return {"objective": None, "status": "invalid_processing_times"}

    # Processing entire jobs consecutively gives a feasible no-wait schedule
    # within this horizon. It also supplies a valid disjunction constant.
    horizon = sum(durations.values())
    if not math.isfinite(horizon):
        return {"objective": None, "status": "invalid_horizon"}

    model = pyo.ConcreteModel()

    model.jobs = pyo.Set(initialize=range(num_jobs), ordered=True)
    model.stations = pyo.Set(initialize=range(num_stations), ordered=True)
    model.job_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (first_job, second_job)
            for first_job in range(num_jobs)
            for second_job in range(first_job + 1, num_jobs)
        ],
    )

    model.duration = pyo.Param(
        model.jobs,
        model.stations,
        initialize=durations,
        within=pyo.NonNegativeReals,
    )
    model.horizon = pyo.Param(initialize=horizon)

    model.start = pyo.Var(
        model.jobs, model.stations, domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )
    model.finish = pyo.Var(
        model.jobs, model.stations, domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )
    model.precedes = pyo.Var(
        model.job_pairs, model.stations, domain=pyo.Binary,
    )
    model.makespan = pyo.Var(
        domain=pyo.NonNegativeReals, bounds=(0, horizon),
    )

    def duration_rule(current_model, job, station):
        return (
            current_model.finish[job, station]
            == current_model.start[job, station]
            + current_model.duration[job, station]
        )

    model.operation_duration = pyo.Constraint(
        model.jobs, model.stations, rule=duration_rule,
    )

    def immediate_transfer_rule(current_model, job, station):
        if station == num_stations - 1:
            return pyo.Constraint.Skip
        return (
            current_model.start[job, station + 1]
            == current_model.finish[job, station]
        )

    model.immediate_transfer = pyo.Constraint(
        model.jobs, model.stations, rule=immediate_transfer_rule,
    )

    def first_before_second_rule(
        current_model, first_job, second_job, station
    ):
        return (
            current_model.finish[first_job, station]
            <= current_model.start[second_job, station]
            + current_model.horizon
            * (1 - current_model.precedes[first_job, second_job, station])
        )

    model.first_before_second = pyo.Constraint(
        model.job_pairs, model.stations, rule=first_before_second_rule,
    )

    def second_before_first_rule(
        current_model, first_job, second_job, station
    ):
        return (
            current_model.finish[second_job, station]
            <= current_model.start[first_job, station]
            + current_model.horizon
            * current_model.precedes[first_job, second_job, station]
        )

    model.second_before_first = pyo.Constraint(
        model.job_pairs, model.stations, rule=second_before_first_rule,
    )

    def makespan_rule(current_model, job):
        return (
            current_model.makespan
            >= current_model.finish[job, num_stations - 1]
        )

    model.completion_bound = pyo.Constraint(
        model.jobs, rule=makespan_rule,
    )
    model.total_completion_time = pyo.Objective(
        expr=model.makespan, sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_completion_time))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}