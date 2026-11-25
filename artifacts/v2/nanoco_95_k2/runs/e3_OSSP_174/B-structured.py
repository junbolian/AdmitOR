# IR: {"sets":{"J":[0,1,2],"W":[0,1,2],"T":"J x W","P":"unordered pairs (a,b) of distinct tasks sharing a component or workstation"},"params":{"processing_time":"params['processing_time'][j][w], nonnegative durations","H":"sum(processing_time[j][w] for (j,w) in T)"},"variables":{"start[t]":"continuous, 0 <= start[t] <= H","precedes[a,b]":"binary for (a,b) in P","makespan":"continuous, 0 <= makespan <= H"},"constraints":["start[j,w] + processing_time[j][w] <= makespan for (j,w) in T","start[a] + processing_time[a] <= start[b] + H*(1-precedes[a,b]) for (a,b) in P","start[b] + processing_time[b] <= start[a] + H*precedes[a,b] for (a,b) in P"],"objective":"minimize makespan"}

import math
from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    processing_time = params["processing_time"]

    components = range(3)
    workstations = range(3)
    tasks = [
        (component, workstation)
        for component in components
        for workstation in workstations
    ]

    durations = {
        (component, workstation): float(
            processing_time[component][workstation]
        )
        for component, workstation in tasks
    }

    if any(
        not math.isfinite(duration) or duration < 0
        for duration in durations.values()
    ):
        raise ValueError("processing_time must contain finite nonnegative values.")

    horizon = sum(durations.values())

    conflicting_pairs = [
        (component_a, workstation_a, component_b, workstation_b)
        for (component_a, workstation_a), (component_b, workstation_b)
        in combinations(tasks, 2)
        if component_a == component_b or workstation_a == workstation_b
    ]

    model = pyo.ConcreteModel()
    model.task_set = pyo.Set(dimen=2, initialize=tasks, ordered=True)
    model.conflict_set = pyo.Set(
        dimen=4, initialize=conflicting_pairs, ordered=True
    )

    model.duration = pyo.Param(
        model.task_set,
        initialize=durations,
        within=pyo.NonNegativeReals,
    )
    model.start = pyo.Var(
        model.task_set,
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )
    model.precedes = pyo.Var(model.conflict_set, domain=pyo.Binary)
    model.makespan = pyo.Var(
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )

    def completion_rule(model, component, workstation):
        return (
            model.start[component, workstation]
            + model.duration[component, workstation]
            <= model.makespan
        )

    model.completion_limit = pyo.Constraint(
        model.task_set, rule=completion_rule
    )

    def forward_rule(
        model, component_a, workstation_a, component_b, workstation_b
    ):
        return (
            model.start[component_a, workstation_a]
            + model.duration[component_a, workstation_a]
            <= model.start[component_b, workstation_b]
            + horizon
            * (
                1
                - model.precedes[
                    component_a, workstation_a, component_b, workstation_b
                ]
            )
        )

    model.forward_separation = pyo.Constraint(
        model.conflict_set, rule=forward_rule
    )

    def reverse_rule(
        model, component_a, workstation_a, component_b, workstation_b
    ):
        return (
            model.start[component_b, workstation_b]
            + model.duration[component_b, workstation_b]
            <= model.start[component_a, workstation_a]
            + horizon
            * model.precedes[
                component_a, workstation_a, component_b, workstation_b
            ]
        )

    model.reverse_separation = pyo.Constraint(
        model.conflict_set, rule=reverse_rule
    )

    model.total_cycle_time = pyo.Objective(
        expr=model.makespan,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cycle_time))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}