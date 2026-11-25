# IR: {"sets":{"jobs":[0,1,2],"stations":[0,1,2],"pairs":[[0,1],[0,2],[1,2]]},"params":{"p[j,k]":"params['processing_times'][j][k], nonnegative","H":"sum(p[j,k] for all jobs and stations)"},"variables":{"start[j,k]":"continuous [0,H]","finish[j,k]":"continuous [0,H]","before[a,b,k]":"binary for a<b","makespan":"continuous [0,H]"},"constraints":["finish[j,k] = start[j,k] + p[j,k]","start[j,k+1] >= finish[j,k] for k=0,1 (zero transfer time)","start[b,k] >= finish[a,k] - H*(1-before[a,b,k]) for a<b","start[a,k] >= finish[b,k] - H*before[a,b,k] for a<b","makespan >= finish[j,2] for every job"],"objective":"minimize makespan"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    processing_times = params["processing_times"]

    model = pyo.ConcreteModel()

    model.jobs = pyo.RangeSet(0, 2)
    model.stations = pyo.RangeSet(0, 2)
    model.transitions = pyo.RangeSet(0, 1)
    model.job_pairs = pyo.Set(
        dimen=2,
        initialize=[(0, 1), (0, 2), (1, 2)],
    )

    model.processing_duration = pyo.Param(
        model.jobs,
        model.stations,
        initialize={
            (job, station): processing_times[job][station]
            for job in model.jobs
            for station in model.stations
        },
        within=pyo.NonNegativeReals,
    )

    # Processing every operation serially gives a valid finite horizon.
    horizon = sum(
        float(pyo.value(model.processing_duration[job, station]))
        for job in model.jobs
        for station in model.stations
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

    def duration_rule(instance, job, station):
        return (
            instance.finish[job, station]
            == instance.start[job, station]
            + instance.processing_duration[job, station]
        )

    model.operation_duration = pyo.Constraint(
        model.jobs,
        model.stations,
        rule=duration_rule,
    )

    def route_rule(instance, job, station):
        return (
            instance.start[job, station + 1]
            >= instance.finish[job, station]
        )

    model.route_precedence = pyo.Constraint(
        model.jobs,
        model.transitions,
        rule=route_rule,
    )

    def first_before_second_rule(instance, first_job, second_job, station):
        return (
            instance.start[second_job, station]
            >= instance.finish[first_job, station]
            - horizon * (1 - instance.before[first_job, second_job, station])
        )

    model.first_before_second = pyo.Constraint(
        model.job_pairs,
        model.stations,
        rule=first_before_second_rule,
    )

    def second_before_first_rule(instance, first_job, second_job, station):
        return (
            instance.start[first_job, station]
            >= instance.finish[second_job, station]
            - horizon * instance.before[first_job, second_job, station]
        )

    model.second_before_first = pyo.Constraint(
        model.job_pairs,
        model.stations,
        rule=second_before_first_rule,
    )

    def makespan_rule(instance, job):
        return instance.makespan >= instance.finish[job, 2]

    model.final_completion = pyo.Constraint(
        model.jobs,
        rule=makespan_rule,
    )

    model.total_cycle_time = pyo.Objective(
        expr=model.makespan,
        sense=pyo.minimize,
    )

    solver_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        # Appsi can raise when no feasible solution is available to load.
        solver_failed = True

    try:
        obj_val = float(pyo.value(model.total_cycle_time))
    except ValueError:
        return {
            "objective": None,
            "status": "solver_failed" if solver_failed else "objective_unavailable",
        }

    return {"objective": obj_val, "status": "optimal"}