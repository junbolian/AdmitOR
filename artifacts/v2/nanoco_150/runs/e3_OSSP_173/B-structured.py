# IR: {"sets":{"J":[0,1,2],"M":[0,1,2],"O":"J x M","P":"unordered pairs ((j,k),(q,r)) in O with j=q or k=r"},"params":{"p[j,k]":"params['processing_times'][j][k], nonnegative","H":"sum(p[j,k] for (j,k) in O)"},"variables":{"start[j,k]":"continuous [0,H]","order[j,k,q,r]":"binary for pairs in P","finish_time":"continuous [0,H]"},"constraints":["start[j,k]+p[j,k] <= finish_time for every operation","start[j,k]+p[j,k] <= start[q,r]+H*(1-order[j,k,q,r]) for every pair in P","start[q,r]+p[q,r] <= start[j,k]+H*order[j,k,q,r] for every pair in P"],"objective":"minimize finish_time"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    jobs = range(3)
    stations = range(3)
    operations = [(job, station) for job in jobs for station in stations]

    durations = {
        (job, station): float(params["processing_times"][job][station])
        for job, station in operations
    }
    horizon = sum(durations.values())

    conflicting_pairs = [
        (job_a, station_a, job_b, station_b)
        for (job_a, station_a), (job_b, station_b) in combinations(operations, 2)
        if job_a == job_b or station_a == station_b
    ]

    model = pyo.ConcreteModel()
    model.jobs = pyo.Set(initialize=jobs, ordered=True)
    model.stations = pyo.Set(initialize=stations, ordered=True)
    model.operations = pyo.Set(dimen=2, initialize=operations, ordered=True)
    model.conflicting_pairs = pyo.Set(
        dimen=4, initialize=conflicting_pairs, ordered=True
    )

    model.duration = pyo.Param(
        model.operations,
        initialize=durations,
        within=pyo.NonNegativeReals,
    )
    model.horizon = pyo.Param(
        initialize=horizon,
        within=pyo.NonNegativeReals,
    )

    model.start = pyo.Var(
        model.operations,
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )
    model.order = pyo.Var(model.conflicting_pairs, domain=pyo.Binary)
    model.finish_time = pyo.Var(
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )

    def completion_rule(model, job, station):
        return (
            model.start[job, station] + model.duration[job, station]
            <= model.finish_time
        )

    model.completion_constraints = pyo.Constraint(
        model.operations, rule=completion_rule
    )

    def first_before_second_rule(
        model, job_a, station_a, job_b, station_b
    ):
        return (
            model.start[job_a, station_a] + model.duration[job_a, station_a]
            <= model.start[job_b, station_b]
            + model.horizon
            * (1 - model.order[job_a, station_a, job_b, station_b])
        )

    model.first_before_second_constraints = pyo.Constraint(
        model.conflicting_pairs, rule=first_before_second_rule
    )

    def second_before_first_rule(
        model, job_a, station_a, job_b, station_b
    ):
        return (
            model.start[job_b, station_b] + model.duration[job_b, station_b]
            <= model.start[job_a, station_a]
            + model.horizon
            * model.order[job_a, station_a, job_b, station_b]
        )

    model.second_before_first_constraints = pyo.Constraint(
        model.conflicting_pairs, rule=second_before_first_rule
    )

    model.total_cycle_time = pyo.Objective(
        expr=model.finish_time,
        sense=pyo.minimize,
    )

    solver_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        # APPsi can raise RuntimeError when no feasible solution can be loaded.
        solver_failed = True

    try:
        obj_val = float(pyo.value(model.total_cycle_time))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": "solver_failed" if solver_failed else "objective_unavailable",
        }

    return {"objective": obj_val, "status": "optimal"}