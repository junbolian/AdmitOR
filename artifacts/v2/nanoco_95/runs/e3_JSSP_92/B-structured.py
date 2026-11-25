# IR: {"sets":{"tasks":[0,1,2],"steps":[0,1,2],"operations":"tasks x steps","routes":[[1,0,2],[2,1,0],[2,1,0]],"conflicts":"unordered pairs of operations assigned to the same robot"},"params":{"processing_times":"params['processing_times'][task][step], nonnegative","H":"sum of all processing_times"},"variables":{"start[task,step]":"continuous, 0 <= start <= H-processing_times[task][step]","before[a,b,c,d]":"binary for each conflict ((a,b),(c,d))","makespan":"continuous, 0 <= makespan <= H"},"constraints":["start[t,k+1] >= start[t,k] + processing_times[t][k] for k < 2","start[a,b] + processing_times[a][b] <= start[c,d] + H*(1-before[a,b,c,d]) for each conflict","start[c,d] + processing_times[c][d] <= start[a,b] + H*before[a,b,c,d] for each conflict","makespan >= start[t,2] + processing_times[t][2] for each task"],"objective":"minimize makespan"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    tasks = range(3)
    steps = range(3)
    routes = (
        (1, 0, 2),
        (2, 1, 0),
        (2, 1, 0),
    )

    processing_times = params["processing_times"]
    durations = {
        (task, step): float(processing_times[task][step])
        for task in tasks
        for step in steps
    }
    horizon = sum(durations.values())

    operations = [(task, step) for task in tasks for step in steps]
    conflicts = [
        (left_task, left_step, right_task, right_step)
        for position, (left_task, left_step) in enumerate(operations)
        for right_task, right_step in operations[position + 1:]
        if routes[left_task][left_step] == routes[right_task][right_step]
    ]

    model = pyo.ConcreteModel()

    model.tasks = pyo.Set(initialize=tasks, ordered=True)
    model.steps = pyo.Set(initialize=steps, ordered=True)
    model.operations = pyo.Set(
        dimen=2, initialize=operations, ordered=True
    )
    model.conflicts = pyo.Set(
        dimen=4, initialize=conflicts, ordered=True
    )
    model.processing_duration = pyo.Param(
        model.operations,
        initialize=durations,
        within=pyo.NonNegativeReals,
    )
    model.horizon = pyo.Param(
        initialize=horizon,
        within=pyo.NonNegativeReals,
    )

    def start_bounds(instance, task, step):
        return (0, horizon - durations[task, step])

    model.start = pyo.Var(
        model.operations,
        domain=pyo.NonNegativeReals,
        bounds=start_bounds,
    )
    model.before = pyo.Var(model.conflicts, domain=pyo.Binary)
    model.makespan = pyo.Var(
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )

    def precedence_rule(instance, task, step):
        if step == 2:
            return pyo.Constraint.Skip
        return (
            instance.start[task, step + 1]
            >= instance.start[task, step]
            + instance.processing_duration[task, step]
        )

    model.task_precedence = pyo.Constraint(
        model.tasks, model.steps, rule=precedence_rule
    )

    def left_first_rule(
        instance, left_task, left_step, right_task, right_step
    ):
        return (
            instance.start[left_task, left_step]
            + instance.processing_duration[left_task, left_step]
            <= instance.start[right_task, right_step]
            + instance.horizon
            * (
                1
                - instance.before[
                    left_task, left_step, right_task, right_step
                ]
            )
        )

    def right_first_rule(
        instance, left_task, left_step, right_task, right_step
    ):
        return (
            instance.start[right_task, right_step]
            + instance.processing_duration[right_task, right_step]
            <= instance.start[left_task, left_step]
            + instance.horizon
            * instance.before[
                left_task, left_step, right_task, right_step
            ]
        )

    model.robot_left_first = pyo.Constraint(
        model.conflicts, rule=left_first_rule
    )
    model.robot_right_first = pyo.Constraint(
        model.conflicts, rule=right_first_rule
    )

    def completion_rule(instance, task):
        return (
            instance.makespan
            >= instance.start[task, 2]
            + instance.processing_duration[task, 2]
        )

    model.task_completion = pyo.Constraint(
        model.tasks, rule=completion_rule
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
    except ValueError:
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}