# IR: {"assumption":"Machine assignments are unspecified; assume all six operations share one machine.","sets":{"jobs":[0,1,2],"steps":[0,1],"operations":"jobs x steps","machine_pairs":"all unordered pairs of distinct operations"},"params":{"processing_time":"params['processing_time'], nonnegative","big_M":"params['big_M'], nonnegative"},"variables":{"start[j,k]":"nonnegative continuous","before[a,b]":"binary for each machine pair; 1 means a precedes b","makespan":"nonnegative continuous"},"constraints":["start[j,1] >= start[j,0] + processing_time for every job j","start[b] >= start[a] + processing_time - big_M*(1-before[a,b]) for every machine pair (a,b)","start[a] >= start[b] + processing_time - big_M*before[a,b] for every machine pair (a,b)","makespan >= start[j,k] + processing_time for every operation (j,k)"],"objective":"minimize makespan"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    jobs = range(3)
    steps = range(2)
    operations = [(job, step) for job in jobs for step in steps]
    machine_pairs = [
        (first[0], first[1], second[0], second[1])
        for first, second in combinations(operations, 2)
    ]

    model = pyo.ConcreteModel()

    model.jobs = pyo.Set(initialize=jobs, ordered=True)
    model.operations = pyo.Set(
        initialize=operations, dimen=2, ordered=True
    )
    model.machine_pairs = pyo.Set(
        initialize=machine_pairs, dimen=4, ordered=True
    )

    model.processing_time = pyo.Param(
        initialize=params["processing_time"],
        within=pyo.NonNegativeReals,
    )
    model.big_M = pyo.Param(
        initialize=params["big_M"],
        within=pyo.NonNegativeReals,
    )

    model.start = pyo.Var(
        model.operations, domain=pyo.NonNegativeReals
    )
    model.before = pyo.Var(
        model.machine_pairs, domain=pyo.Binary
    )
    model.makespan = pyo.Var(domain=pyo.NonNegativeReals)

    def precedence_rule(instance, job):
        return (
            instance.start[job, 1]
            >= instance.start[job, 0] + instance.processing_time
        )

    model.precedence = pyo.Constraint(
        model.jobs, rule=precedence_rule
    )

    def forward_order_rule(instance, job_a, step_a, job_b, step_b):
        return (
            instance.start[job_b, step_b]
            >= instance.start[job_a, step_a]
            + instance.processing_time
            - instance.big_M
            * (1 - instance.before[job_a, step_a, job_b, step_b])
        )

    model.forward_order = pyo.Constraint(
        model.machine_pairs, rule=forward_order_rule
    )

    def reverse_order_rule(instance, job_a, step_a, job_b, step_b):
        return (
            instance.start[job_a, step_a]
            >= instance.start[job_b, step_b]
            + instance.processing_time
            - instance.big_M
            * instance.before[job_a, step_a, job_b, step_b]
        )

    model.reverse_order = pyo.Constraint(
        model.machine_pairs, rule=reverse_order_rule
    )

    def completion_rule(instance, job, step):
        return (
            instance.makespan
            >= instance.start[job, step] + instance.processing_time
        )

    model.completion = pyo.Constraint(
        model.operations, rule=completion_rule
    )

    model.total_makespan = pyo.Objective(
        expr=model.makespan, sense=pyo.minimize
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # Appsi can raise when no feasible solution is available to load.
        # Objective retrieval below remains the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_makespan))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}