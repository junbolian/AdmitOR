# IR: {"sets":{"jobs":[0,1,2],"stations":[0,1,2],"operations":"jobs x stations","conflicts":"unordered pairs of distinct operations sharing a job or station"},"params":{"processing_times":"nonnegative 3x3 matrix read from params","H":"sum of all processing_times"},"variables":{"start[j,s]":"continuous, nonnegative","precedes[a,b]":"binary for each conflict (a,b)","makespan":"continuous in [0,H]"},"constraints":["start[j,s] + processing_times[j,s] <= makespan for every operation","start[a] + processing_times[a] <= start[b] + H*(1-precedes[a,b]) for every conflict","start[b] + processing_times[b] <= start[a] + H*precedes[a,b] for every conflict"],"objective":"minimize makespan"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    jobs = range(3)
    stations = range(3)
    operations = [(job, station) for job in jobs for station in stations]
    conflicts = [
        (job_a, station_a, job_b, station_b)
        for (job_a, station_a), (job_b, station_b) in combinations(operations, 2)
        if job_a == job_b or station_a == station_b
    ]

    model = pyo.ConcreteModel()

    model.jobs = pyo.Set(initialize=jobs, ordered=True)
    model.stations = pyo.Set(initialize=stations, ordered=True)
    model.operations = pyo.Set(dimen=2, initialize=operations, ordered=True)
    model.conflicts = pyo.Set(dimen=4, initialize=conflicts, ordered=True)

    model.processing_times = pyo.Param(
        model.operations,
        initialize={
            (job, station): params["processing_times"][job][station]
            for job, station in operations
        },
        within=pyo.NonNegativeReals,
    )

    # Processing every operation sequentially provides a valid horizon.
    model.horizon = pyo.Param(
        initialize=sum(
            pyo.value(model.processing_times[job, station])
            for job, station in operations
        ),
        within=pyo.NonNegativeReals,
    )

    model.start = pyo.Var(model.operations, domain=pyo.NonNegativeReals)
    model.precedes = pyo.Var(model.conflicts, domain=pyo.Binary)
    model.makespan = pyo.Var(
        domain=pyo.NonNegativeReals,
        bounds=(0, pyo.value(model.horizon)),
    )

    def completion_rule(mdl, job, station):
        return (
            mdl.start[job, station] + mdl.processing_times[job, station]
            <= mdl.makespan
        )

    model.completion_limits = pyo.Constraint(
        model.operations, rule=completion_rule
    )

    def forward_rule(mdl, job_a, station_a, job_b, station_b):
        return (
            mdl.start[job_a, station_a]
            + mdl.processing_times[job_a, station_a]
            <= mdl.start[job_b, station_b]
            + mdl.horizon
            * (1 - mdl.precedes[job_a, station_a, job_b, station_b])
        )

    model.forward_nonoverlap = pyo.Constraint(
        model.conflicts, rule=forward_rule
    )

    def reverse_rule(mdl, job_a, station_a, job_b, station_b):
        return (
            mdl.start[job_b, station_b]
            + mdl.processing_times[job_b, station_b]
            <= mdl.start[job_a, station_a]
            + mdl.horizon
            * mdl.precedes[job_a, station_a, job_b, station_b]
        )

    model.reverse_nonoverlap = pyo.Constraint(
        model.conflicts, rule=reverse_rule
    )

    model.makespan_objective = pyo.Objective(
        expr=model.makespan, sense=pyo.minimize
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        # APPsi raises this error when it cannot load a feasible solution.
        if "a feasible solution was not found" in str(error).lower():
            return {"objective": None, "status": "infeasible_or_failed"}
        raise

    try:
        obj_val = float(pyo.value(model.makespan_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}