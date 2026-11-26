# IR: {"sets":{"workers":["I","II","III","IV","V"],"tasks":["A","B","C","D"]},"params":{"time[worker,task]":"params[f'time_{worker}_{task}']"},"variables":{"assigned[worker,task]":"binary"},"constraints":["For each task: sum(assigned[worker,task] for worker in workers) == 1","For each worker: sum(assigned[worker,task] for task in tasks) <= 1"],"objective":"minimize sum(time[worker,task] * assigned[worker,task] for worker in workers for task in tasks)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    workers = ("I", "II", "III", "IV", "V")
    tasks = ("A", "B", "C", "D")

    processing_times = {
        (worker, task): params[f"time_{worker}_{task}"]
        for worker in workers
        for task in tasks
    }

    model = pyo.ConcreteModel()
    model.workers = pyo.Set(initialize=workers, ordered=True)
    model.tasks = pyo.Set(initialize=tasks, ordered=True)

    model.processing_time = pyo.Param(
        model.workers,
        model.tasks,
        initialize=processing_times,
        within=pyo.Reals,
    )

    model.assigned = pyo.Var(
        model.workers,
        model.tasks,
        domain=pyo.Binary,
    )

    def task_assignment_rule(instance, task):
        return sum(
            instance.assigned[worker, task]
            for worker in instance.workers
        ) == 1

    model.task_assignment = pyo.Constraint(
        model.tasks,
        rule=task_assignment_rule,
    )

    def worker_capacity_rule(instance, worker):
        return sum(
            instance.assigned[worker, task]
            for task in instance.tasks
        ) <= 1

    model.worker_capacity = pyo.Constraint(
        model.workers,
        rule=worker_capacity_rule,
    )

    model.total_hours = pyo.Objective(
        expr=sum(
            model.processing_time[worker, task] * model.assigned[worker, task]
            for worker in model.workers
            for task in model.tasks
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_hours))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}