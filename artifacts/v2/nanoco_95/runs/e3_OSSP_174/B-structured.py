# IR: {
#   "sets": {"J": ["J0", "J1", "J2"], "W": ["M0", "M1", "M2"], "O": "J x W", "K": "unordered pairs of distinct operations sharing a component or workstation"},
#   "params": {"duration[j,w]": "params['duration_' + j + '_' + w], nonnegative", "H": "sum(duration[j,w] for (j,w) in O)"},
#   "variables": {"start[j,w]": "continuous, 0 <= start[j,w] <= H-duration[j,w]", "before[a,b]": "binary for (a,b) in K", "makespan": "continuous, 0 <= makespan <= H"},
#   "constraints": [
#     "start[a] + duration[a] <= start[b] + H*(1-before[a,b]) for (a,b) in K",
#     "start[b] + duration[b] <= start[a] + H*before[a,b] for (a,b) in K",
#     "start[j,w] + duration[j,w] <= makespan for (j,w) in O"
#   ],
#   "objective": "minimize makespan"
# }

from itertools import combinations

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    jobs = ("J0", "J1", "J2")
    workstations = ("M0", "M1", "M2")
    operations = [
        (job, station)
        for job in jobs
        for station in workstations
    ]

    durations = {
        ("J0", "M0"): float(params["duration_J0_M0"]),
        ("J0", "M1"): float(params["duration_J0_M1"]),
        ("J0", "M2"): float(params["duration_J0_M2"]),
        ("J1", "M0"): float(params["duration_J1_M0"]),
        ("J1", "M1"): float(params["duration_J1_M1"]),
        ("J1", "M2"): float(params["duration_J1_M2"]),
        ("J2", "M0"): float(params["duration_J2_M0"]),
        ("J2", "M1"): float(params["duration_J2_M1"]),
        ("J2", "M2"): float(params["duration_J2_M2"]),
    }
    horizon = sum(durations.values())

    conflict_pairs = [
        (first[0], first[1], second[0], second[1])
        for first, second in combinations(operations, 2)
        if first[0] == second[0] or first[1] == second[1]
    ]

    model = pyo.ConcreteModel()

    model.jobs = pyo.Set(initialize=jobs, ordered=True)
    model.workstations = pyo.Set(initialize=workstations, ordered=True)
    model.operations = pyo.Set(
        dimen=2, initialize=operations, ordered=True
    )
    model.conflict_pairs = pyo.Set(
        dimen=4, initialize=conflict_pairs, ordered=True
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

    def start_bounds(instance, job, station):
        return (
            0,
            pyo.value(instance.horizon - instance.duration[job, station]),
        )

    model.start = pyo.Var(
        model.operations,
        domain=pyo.NonNegativeReals,
        bounds=start_bounds,
    )
    model.before = pyo.Var(
        model.conflict_pairs,
        domain=pyo.Binary,
    )
    model.makespan = pyo.Var(
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )

    def first_before_second(
        instance, first_job, first_station, second_job, second_station
    ):
        return (
            instance.start[first_job, first_station]
            + instance.duration[first_job, first_station]
            <= instance.start[second_job, second_station]
            + instance.horizon
            * (
                1
                - instance.before[
                    first_job, first_station, second_job, second_station
                ]
            )
        )

    def second_before_first(
        instance, first_job, first_station, second_job, second_station
    ):
        return (
            instance.start[second_job, second_station]
            + instance.duration[second_job, second_station]
            <= instance.start[first_job, first_station]
            + instance.horizon
            * instance.before[
                first_job, first_station, second_job, second_station
            ]
        )

    model.first_precedence = pyo.Constraint(
        model.conflict_pairs, rule=first_before_second
    )
    model.second_precedence = pyo.Constraint(
        model.conflict_pairs, rule=second_before_first
    )

    def completion_bound(instance, job, station):
        return (
            instance.start[job, station] + instance.duration[job, station]
            <= instance.makespan
        )

    model.completion_bounds = pyo.Constraint(
        model.operations, rule=completion_bound
    )
    model.objective = pyo.Objective(
        expr=model.makespan,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}