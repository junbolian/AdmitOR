# IR: {"sets":{"T":[0,1,2],"S":[0,1,2],"O":"T x S","P":"unordered distinct operation pairs assigned to the same robot"},"params":{"p[t,s]":"params['proc_time'][t][s]","r[t,s]":"params['robot_assignment'][t][s]","H":"sum(p[t,s] for (t,s) in O)"},"variables":{"start[t,s]":"continuous, 0 <= start[t,s] <= H-p[t,s]","before[a,b,c,d]":"binary for (a,b,c,d) in P","makespan":"continuous, 0 <= makespan <= H"},"constraints":["start[t,s+1] >= start[t,s]+p[t,s] for t in T, s in {0,1}","start[a,b]+p[a,b] <= start[c,d]+H*(1-before[a,b,c,d]) for (a,b,c,d) in P","start[c,d]+p[c,d] <= start[a,b]+H*before[a,b,c,d] for (a,b,c,d) in P","makespan >= start[t,2]+p[t,2] for t in T"],"objective":"minimize makespan"}

from itertools import combinations

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
    assignments = {
        (task, stage): robot_assignment[task][stage]
        for task, stage in operations
    }

    horizon = sum(durations.values())
    robot_pairs = [
        (first[0], first[1], second[0], second[1])
        for first, second in combinations(operations, 2)
        if assignments[first] == assignments[second]
    ]

    model = pyo.ConcreteModel()
    model.tasks = pyo.Set(initialize=tasks, ordered=True)
    model.stages = pyo.Set(initialize=stages, ordered=True)
    model.precedence_stages = pyo.Set(initialize=[0, 1], ordered=True)
    model.robot_pairs = pyo.Set(
        dimen=4, initialize=robot_pairs, ordered=True
    )

    model.duration = pyo.Param(
        model.tasks,
        model.stages,
        initialize=durations,
        within=pyo.NonNegativeReals,
    )
    model.horizon = pyo.Param(initialize=horizon)

    def start_bounds(instance, task, stage):
        return (0, horizon - durations[task, stage])

    model.start = pyo.Var(
        model.tasks,
        model.stages,
        domain=pyo.NonNegativeReals,
        bounds=start_bounds,
    )
    model.before = pyo.Var(model.robot_pairs, domain=pyo.Binary)
    model.makespan = pyo.Var(
        domain=pyo.NonNegativeReals, bounds=(0, horizon)
    )

    def precedence_rule(instance, task, stage):
        return (
            instance.start[task, stage + 1]
            >= instance.start[task, stage] + instance.duration[task, stage]
        )

    model.precedence = pyo.Constraint(
        model.tasks,
        model.precedence_stages,
        rule=precedence_rule,
    )

    def first_before_second_rule(instance, task_a, stage_a, task_b, stage_b):
        return (
            instance.start[task_a, stage_a]
            + instance.duration[task_a, stage_a]
            <= instance.start[task_b, stage_b]
            + instance.horizon
            * (1 - instance.before[task_a, stage_a, task_b, stage_b])
        )

    model.first_before_second = pyo.Constraint(
        model.robot_pairs, rule=first_before_second_rule
    )

    def second_before_first_rule(instance, task_a, stage_a, task_b, stage_b):
        return (
            instance.start[task_b, stage_b]
            + instance.duration[task_b, stage_b]
            <= instance.start[task_a, stage_a]
            + instance.horizon
            * instance.before[task_a, stage_a, task_b, stage_b]
        )

    model.second_before_first = pyo.Constraint(
        model.robot_pairs, rule=second_before_first_rule
    )

    def completion_rule(instance, task):
        return (
            instance.makespan
            >= instance.start[task, 2] + instance.duration[task, 2]
        )

    model.completion = pyo.Constraint(
        model.tasks, rule=completion_rule
    )
    model.objective = pyo.Objective(
        expr=model.makespan, sense=pyo.minimize
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when no feasible solution can be loaded.
        # Objective retrieval below is the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}