# IR: {
#   "sets": {"J": [0,1,2], "O": [0,1], "A": "J x O", "P": "unordered pairs (a,b) in A with a < b"},
#   "assumption": "Machine assignments are unspecified; all six operations are assumed to share one machine.",
#   "params": {
#     "p[0,0]": "processing_time_j0_o0",
#     "p[0,1]": "processing_time_j0_o1",
#     "p[1,0]": "processing_time_j1_o0",
#     "p[1,1]": "processing_time_j1_o1",
#     "p[2,0]": "processing_time_j2_o0",
#     "p[2,1]": "processing_time_j2_o1",
#     "lag[0]": "precedence_lag_j0",
#     "lag[1]": "precedence_lag_j1",
#     "lag[2]": "precedence_lag_j2",
#     "M": "machine_disjunctive_bigM"
#   },
#   "variables": {"s[a]": "nonnegative continuous", "C": "nonnegative continuous", "y[a,b]": "binary for (a,b) in P; 1 means a precedes b"},
#   "constraints": [
#     "s[j,1] >= s[j,0] + p[j,0] + lag[j] for j in J",
#     "s[b] >= s[a] + p[a] - M*(1-y[a,b]) for (a,b) in P",
#     "s[a] >= s[b] + p[b] - M*y[a,b] for (a,b) in P",
#     "C >= s[a] + p[a] for a in A"
#   ],
#   "objective": "minimize C"
# }

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    processing_times = {
        (0, 0): params["processing_time_j0_o0"],
        (0, 1): params["processing_time_j0_o1"],
        (1, 0): params["processing_time_j1_o0"],
        (1, 1): params["processing_time_j1_o1"],
        (2, 0): params["processing_time_j2_o0"],
        (2, 1): params["processing_time_j2_o1"],
    }
    precedence_lags = {
        0: params["precedence_lag_j0"],
        1: params["precedence_lag_j1"],
        2: params["precedence_lag_j2"],
    }
    big_m = params["machine_disjunctive_bigM"]

    operations = [(job, operation) for job in range(3) for operation in range(2)]
    machine_pairs = [
        (first[0], first[1], second[0], second[1])
        for first, second in combinations(operations, 2)
    ]

    model = pyo.ConcreteModel()

    model.jobs = pyo.Set(initialize=range(3), ordered=True)
    model.operations = pyo.Set(dimen=2, initialize=operations, ordered=True)
    model.machine_pairs = pyo.Set(
        dimen=4, initialize=machine_pairs, ordered=True
    )

    model.processing_time = pyo.Param(
        model.operations, initialize=processing_times
    )
    model.precedence_lag = pyo.Param(
        model.jobs, initialize=precedence_lags
    )
    model.big_m = pyo.Param(initialize=big_m)

    model.start_time = pyo.Var(
        model.operations, domain=pyo.NonNegativeReals
    )
    model.makespan = pyo.Var(domain=pyo.NonNegativeReals)
    model.precedes = pyo.Var(model.machine_pairs, domain=pyo.Binary)

    def precedence_rule(schedule, job):
        return (
            schedule.start_time[job, 1]
            >= schedule.start_time[job, 0]
            + schedule.processing_time[job, 0]
            + schedule.precedence_lag[job]
        )

    model.job_precedence = pyo.Constraint(
        model.jobs, rule=precedence_rule
    )

    def forward_capacity_rule(schedule, job_a, operation_a, job_b, operation_b):
        return (
            schedule.start_time[job_b, operation_b]
            >= schedule.start_time[job_a, operation_a]
            + schedule.processing_time[job_a, operation_a]
            - schedule.big_m
            * (1 - schedule.precedes[job_a, operation_a, job_b, operation_b])
        )

    model.forward_capacity = pyo.Constraint(
        model.machine_pairs, rule=forward_capacity_rule
    )

    def reverse_capacity_rule(schedule, job_a, operation_a, job_b, operation_b):
        return (
            schedule.start_time[job_a, operation_a]
            >= schedule.start_time[job_b, operation_b]
            + schedule.processing_time[job_b, operation_b]
            - schedule.big_m
            * schedule.precedes[job_a, operation_a, job_b, operation_b]
        )

    model.reverse_capacity = pyo.Constraint(
        model.machine_pairs, rule=reverse_capacity_rule
    )

    def completion_rule(schedule, job, operation):
        return (
            schedule.makespan
            >= schedule.start_time[job, operation]
            + schedule.processing_time[job, operation]
        )

    model.completion_bounds = pyo.Constraint(
        model.operations, rule=completion_rule
    )

    model.makespan_objective = pyo.Objective(
        expr=model.makespan, sense=pyo.minimize
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" not in str(exc).lower():
            raise
        # HiGHS can raise when it cannot load a solution.
        # Objective retrieval below remains the sole success test.

    try:
        obj_val = float(pyo.value(model.makespan_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}