# IR: {
#   "sets": {"J": [0, 1, 2], "O": [0, 1], "A": "J x O", "P": "unordered distinct pairs (a,b) in A, with a lexicographically before b"},
#   "assumption": "Machine assignments are unspecified; all six operations share one machine, so machine constraints apply to every pair. No additional machine setup time is specified.",
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
#     "big_M": "machine_disjunctive_bigM"
#   },
#   "variables": {"s[a]": "continuous >= 0", "y[a,b]": "binary; 1 means a precedes b", "C": "continuous >= 0"},
#   "constraints": [
#     "s[j,1] >= s[j,0] + p[j,0] + lag[j] for j in J",
#     "s[b] >= s[a] + p[a] - big_M*(1-y[a,b]) for (a,b) in P",
#     "s[a] >= s[b] + p[b] - big_M*y[a,b] for (a,b) in P",
#     "C >= s[a] + p[a] for a in A"
#   ],
#   "objective": "minimize C"
# }

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

    operations = [
        (job, operation)
        for job in range(3)
        for operation in range(2)
    ]
    machine_pairs = [
        (*first, *second)
        for position, first in enumerate(operations)
        for second in operations[position + 1:]
    ]

    model = pyo.ConcreteModel()
    model.J = pyo.Set(initialize=range(3), ordered=True)
    model.O = pyo.Set(initialize=range(2), ordered=True)
    model.A = pyo.Set(dimen=2, initialize=operations, ordered=True)
    model.P = pyo.Set(dimen=4, initialize=machine_pairs, ordered=True)

    model.p = pyo.Param(
        model.A, initialize=processing_times, within=pyo.NonNegativeReals
    )
    model.lag = pyo.Param(
        model.J, initialize=precedence_lags, within=pyo.NonNegativeReals
    )
    model.big_M = pyo.Param(
        initialize=big_m, within=pyo.NonNegativeReals
    )

    model.s = pyo.Var(model.A, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, domain=pyo.Binary)
    model.C = pyo.Var(domain=pyo.NonNegativeReals)

    def precedence_rule(instance, job):
        return (
            instance.s[job, 1]
            >= instance.s[job, 0] + instance.p[job, 0] + instance.lag[job]
        )

    model.precedence_constraints = pyo.Constraint(
        model.J, rule=precedence_rule
    )

    def forward_rule(instance, first_job, first_op, second_job, second_op):
        return (
            instance.s[second_job, second_op]
            >= instance.s[first_job, first_op]
            + instance.p[first_job, first_op]
            - instance.big_M
            * (1 - instance.y[first_job, first_op, second_job, second_op])
        )

    model.machine_forward_constraints = pyo.Constraint(
        model.P, rule=forward_rule
    )

    def reverse_rule(instance, first_job, first_op, second_job, second_op):
        return (
            instance.s[first_job, first_op]
            >= instance.s[second_job, second_op]
            + instance.p[second_job, second_op]
            - instance.big_M
            * instance.y[first_job, first_op, second_job, second_op]
        )

    model.machine_reverse_constraints = pyo.Constraint(
        model.P, rule=reverse_rule
    )

    def makespan_rule(instance, job, operation):
        return (
            instance.C
            >= instance.s[job, operation] + instance.p[job, operation]
        )

    model.makespan_constraints = pyo.Constraint(
        model.A, rule=makespan_rule
    )
    model.makespan_objective = pyo.Objective(
        expr=model.C, sense=pyo.minimize
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.makespan_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}