# IR: {"sets":{"workers":[0,1,2,3,4],"tasks":[0,1,2,3]},"params":{"task_times":"5x4 array from params['task_times'], ordered workers I-V and tasks A-D"},"variables":{"assignment[w,t]":"binary"},"constraints":["For each task t: sum_w assignment[w,t] = 1","For each worker w: sum_t assignment[w,t] <= 1"],"objective":"Minimize sum_w sum_t task_times[w][t] * assignment[w,t]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    task_times = params["task_times"]

    model = pyo.ConcreteModel()
    model.workers = pyo.Set(initialize=range(5), ordered=True)
    model.tasks = pyo.Set(initialize=range(4), ordered=True)

    model.processing_time = pyo.Param(
        model.workers,
        model.tasks,
        initialize={
            (worker, task): task_times[worker][task]
            for worker in model.workers
            for task in model.tasks
        },
    )

    model.assignment = pyo.Var(
        model.workers,
        model.tasks,
        domain=pyo.Binary,
    )

    def task_assignment_rule(instance, task):
        return sum(
            instance.assignment[worker, task]
            for worker in instance.workers
        ) == 1

    model.task_assignment = pyo.Constraint(
        model.tasks,
        rule=task_assignment_rule,
    )

    def worker_capacity_rule(instance, worker):
        return sum(
            instance.assignment[worker, task]
            for task in instance.tasks
        ) <= 1

    model.worker_capacity = pyo.Constraint(
        model.workers,
        rule=worker_capacity_rule,
    )

    model.total_time = pyo.Objective(
        expr=sum(
            model.processing_time[worker, task]
            * model.assignment[worker, task]
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
        obj_val = float(pyo.value(model.total_time))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}