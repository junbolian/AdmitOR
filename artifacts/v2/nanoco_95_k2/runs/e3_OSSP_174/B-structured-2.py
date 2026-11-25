# IR: {"sets":{"J":[0,1,2],"M":[0,1,2],"O":"J x M","P":"unordered pairs of distinct operations sharing a job or workstation"},"params":{"p[j,k]":"params['processing_time'][j][k], nonnegative","H":"sum(p[j,k] for (j,k) in O)"},"variables":{"start[j,k]":"continuous, 0 <= start[j,k] <= H-p[j,k]","before[a,b]":"binary for (a,b) in P","makespan":"continuous, 0 <= makespan <= H"},"constraints":["makespan >= start[j,k]+p[j,k] for every operation (j,k)","start[a]+p[a] <= start[b]+H*(1-before[a,b]) for every conflict pair (a,b)","start[b]+p[b] <= start[a]+H*before[a,b] for every conflict pair (a,b)"],"objective":"minimize makespan"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    processing_time = params["processing_time"]
    jobs = range(3)
    workstations = range(3)
    operations = [
        (job, workstation)
        for job in jobs
        for workstation in workstations
    ]
    durations = {
        (job, workstation): float(processing_time[job][workstation])
        for job, workstation in operations
    }

    model = pyo.ConcreteModel()
    model.jobs = pyo.Set(initialize=jobs, ordered=True)
    model.workstations = pyo.Set(initialize=workstations, ordered=True)
    model.operations = pyo.Set(
        dimen=2, initialize=operations, ordered=True
    )
    model.duration = pyo.Param(
        model.operations,
        initialize=durations,
        within=pyo.NonNegativeReals,
    )

    # Scheduling all operations consecutively establishes a valid horizon.
    horizon = sum(
        pyo.value(model.duration[job, workstation])
        for job, workstation in operations
    )
    model.horizon = pyo.Param(
        initialize=horizon, within=pyo.NonNegativeReals
    )

    conflict_pairs = [
        (first_job, first_station, second_job, second_station)
        for (
            (first_job, first_station),
            (second_job, second_station),
        ) in combinations(operations, 2)
        if first_job == second_job or first_station == second_station
    ]
    model.conflict_pairs = pyo.Set(
        dimen=4, initialize=conflict_pairs, ordered=True
    )

    def start_bounds(schedule, job, workstation):
        return (
            0,
            pyo.value(schedule.horizon)
            - pyo.value(schedule.duration[job, workstation]),
        )

    model.start = pyo.Var(
        model.operations,
        domain=pyo.NonNegativeReals,
        bounds=start_bounds,
    )
    model.before = pyo.Var(
        model.conflict_pairs, domain=pyo.Binary
    )
    model.makespan = pyo.Var(
        domain=pyo.NonNegativeReals, bounds=(0, horizon)
    )

    def completion_rule(schedule, job, workstation):
        return (
            schedule.makespan
            >= schedule.start[job, workstation]
            + schedule.duration[job, workstation]
        )

    model.completion_constraints = pyo.Constraint(
        model.operations, rule=completion_rule
    )

    def first_before_second_rule(
        schedule, first_job, first_station, second_job, second_station
    ):
        return (
            schedule.start[first_job, first_station]
            + schedule.duration[first_job, first_station]
            <= schedule.start[second_job, second_station]
            + schedule.horizon
            * (
                1
                - schedule.before[
                    first_job, first_station, second_job, second_station
                ]
            )
        )

    model.first_before_second_constraints = pyo.Constraint(
        model.conflict_pairs, rule=first_before_second_rule
    )

    def second_before_first_rule(
        schedule, first_job, first_station, second_job, second_station
    ):
        return (
            schedule.start[second_job, second_station]
            + schedule.duration[second_job, second_station]
            <= schedule.start[first_job, first_station]
            + schedule.horizon
            * schedule.before[
                first_job, first_station, second_job, second_station
            ]
        )

    model.second_before_first_constraints = pyo.Constraint(
        model.conflict_pairs, rule=second_before_first_rule
    )

    model.total_cycle_time = pyo.Objective(
        expr=model.makespan, sense=pyo.minimize
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cycle_time))
    except ValueError:
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}