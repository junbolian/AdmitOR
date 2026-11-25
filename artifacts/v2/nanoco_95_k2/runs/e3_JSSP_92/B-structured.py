# IR: {"sets":{"T":[0,1,2],"S":[0,1,2],"O":"T x S","P":"unordered pairs (a,b) of distinct operations with robot_assignment[a]=robot_assignment[b]"},"params":{"proc_time":"nonnegative processing times indexed [task][stage]","robot_assignment":"robot indices in {0,1,2}, indexed [task][stage]","H":"sum(proc_time[t][s] for (t,s) in O)"},"variables":{"start[o]":"continuous, 0 <= start[o] <= H-proc_time[o]","before[a,b]":"binary for (a,b) in P","makespan":"continuous, 0 <= makespan <= H"},"constraints":["start[t,s+1] >= start[t,s] + proc_time[t][s] for t in T, s in {0,1}","start[b] >= start[a] + proc_time[a] - H*(1-before[a,b]) for (a,b) in P","start[a] >= start[b] + proc_time[b] - H*before[a,b] for (a,b) in P","makespan >= start[o] + proc_time[o] for o in O"],"objective":"minimize makespan"}

from itertools import combinations
import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    proc_time = params["proc_time"]
    robot_assignment = params["robot_assignment"]

    tasks = range(3)
    stages = range(3)
    operations = [(task, stage) for task in tasks for stage in stages]

    durations = {
        (task, stage): float(proc_time[task][stage])
        for task, stage in operations
    }
    robots = {
        (task, stage): robot_assignment[task][stage]
        for task, stage in operations
    }

    if any(
        not math.isfinite(duration) or duration < 0
        for duration in durations.values()
    ):
        return {"objective": None, "status": "invalid_processing_time"}

    if any(robot not in (0, 1, 2) for robot in robots.values()):
        return {"objective": None, "status": "invalid_robot_assignment"}

    horizon = sum(durations.values())
    if not math.isfinite(horizon):
        return {"objective": None, "status": "invalid_horizon"}

    conflict_pairs = [
        (first[0], first[1], second[0], second[1])
        for first, second in combinations(operations, 2)
        if robots[first] == robots[second]
    ]

    model = pyo.ConcreteModel()
    model.tasks = pyo.Set(initialize=tasks, ordered=True)
    model.stages = pyo.Set(initialize=stages, ordered=True)
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

    def start_bounds(block, task, stage):
        return (0, horizon - durations[task, stage])

    model.start = pyo.Var(
        model.operations,
        domain=pyo.NonNegativeReals,
        bounds=start_bounds,
    )
    model.before = pyo.Var(model.conflict_pairs, domain=pyo.Binary)
    model.makespan = pyo.Var(
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )

    def precedence_rule(block, task, stage):
        return (
            block.start[task, stage + 1]
            >= block.start[task, stage] + block.duration[task, stage]
        )

    model.precedence = pyo.Constraint(
        model.tasks, range(2), rule=precedence_rule
    )

    def first_before_second_rule(
        block, first_task, first_stage, second_task, second_stage
    ):
        return (
            block.start[second_task, second_stage]
            >= block.start[first_task, first_stage]
            + block.duration[first_task, first_stage]
            - horizon
            * (
                1
                - block.before[
                    first_task, first_stage, second_task, second_stage
                ]
            )
        )

    def second_before_first_rule(
        block, first_task, first_stage, second_task, second_stage
    ):
        return (
            block.start[first_task, first_stage]
            >= block.start[second_task, second_stage]
            + block.duration[second_task, second_stage]
            - horizon
            * block.before[
                first_task, first_stage, second_task, second_stage
            ]
        )

    model.first_before_second = pyo.Constraint(
        model.conflict_pairs, rule=first_before_second_rule
    )
    model.second_before_first = pyo.Constraint(
        model.conflict_pairs, rule=second_before_first_rule
    )

    def completion_rule(block, task, stage):
        return (
            block.makespan
            >= block.start[task, stage] + block.duration[task, stage]
        )

    model.completion = pyo.Constraint(
        model.operations, rule=completion_rule
    )
    model.makespan_objective = pyo.Objective(
        expr=model.makespan, sense=pyo.minimize
    )

    failure_reason = "objective_unavailable"
    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when it cannot load a feasible solution.
        # Success is determined exclusively by objective retrieval below.
        failure_reason = "solver_failed"

    try:
        obj_val = float(pyo.value(model.makespan_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": failure_reason}

    return {"objective": obj_val, "status": "optimal"}