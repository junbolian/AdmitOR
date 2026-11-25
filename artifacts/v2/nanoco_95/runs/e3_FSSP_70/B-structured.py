# IR: {"sets":{"jobs":[0,1,2],"stations":[0,1,2],"pairs":"(i,j) with i<j"},"params":{"p[j,k]":"params[\"processing_times\"][j][k]","H":"sum(p[j,k] for all j,k)"},"variables":{"start[j,k]":"continuous [0,H]","finish[j,k]":"continuous [0,H]","before[i,j,k]":"binary for each pair and station","makespan":"continuous [0,H]"},"constraints":["finish[j,k] = start[j,k] + p[j,k]","start[j,1] = finish[j,0] (immediate transfer)","start[j,2] >= finish[j,1]","start[j,k] >= finish[i,k] - H*(1-before[i,j,k]) for i<j","start[i,k] >= finish[j,k] - H*before[i,j,k] for i<j","makespan >= finish[j,2]"],"objective":"minimize makespan"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    processing_times = params["processing_times"]

    model = pyo.ConcreteModel()
    model.jobs = pyo.RangeSet(0, 2)
    model.stations = pyo.RangeSet(0, 2)
    model.job_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (first_job, second_job)
            for first_job in range(3)
            for second_job in range(3)
            if first_job < second_job
        ],
    )

    model.duration = pyo.Param(
        model.jobs,
        model.stations,
        initialize=lambda mdl, job, station: processing_times[job][station],
        within=pyo.NonNegativeReals,
    )

    # Processing every job's complete route serially gives a feasible horizon.
    horizon = float(
        sum(
            pyo.value(model.duration[job, station])
            for job in model.jobs
            for station in model.stations
        )
    )

    model.start = pyo.Var(
        model.jobs,
        model.stations,
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )
    model.finish = pyo.Var(
        model.jobs,
        model.stations,
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )
    model.before = pyo.Var(
        model.job_pairs,
        model.stations,
        domain=pyo.Binary,
    )
    model.makespan = pyo.Var(
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )

    def operation_duration_rule(mdl, job, station):
        return (
            mdl.finish[job, station]
            == mdl.start[job, station] + mdl.duration[job, station]
        )

    model.operation_duration = pyo.Constraint(
        model.jobs,
        model.stations,
        rule=operation_duration_rule,
    )

    # The explicitly immediate transfer is from Station 0 to Station 1.
    def immediate_transfer_rule(mdl, job):
        return mdl.start[job, 1] == mdl.finish[job, 0]

    model.immediate_transfer = pyo.Constraint(
        model.jobs,
        rule=immediate_transfer_rule,
    )

    def final_station_precedence_rule(mdl, job):
        return mdl.start[job, 2] >= mdl.finish[job, 1]

    model.final_station_precedence = pyo.Constraint(
        model.jobs,
        rule=final_station_precedence_rule,
    )

    def first_job_precedes_rule(mdl, first_job, second_job, station):
        return (
            mdl.start[second_job, station]
            >= mdl.finish[first_job, station]
            - horizon * (1 - mdl.before[first_job, second_job, station])
        )

    model.first_job_precedes = pyo.Constraint(
        model.job_pairs,
        model.stations,
        rule=first_job_precedes_rule,
    )

    def second_job_precedes_rule(mdl, first_job, second_job, station):
        return (
            mdl.start[first_job, station]
            >= mdl.finish[second_job, station]
            - horizon * mdl.before[first_job, second_job, station]
        )

    model.second_job_precedes = pyo.Constraint(
        model.job_pairs,
        model.stations,
        rule=second_job_precedes_rule,
    )

    def completion_bound_rule(mdl, job):
        return mdl.makespan >= mdl.finish[job, 2]

    model.completion_bound = pyo.Constraint(
        model.jobs,
        rule=completion_bound_rule,
    )

    model.total_completion_time = pyo.Objective(
        expr=model.makespan,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_completion_time))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}