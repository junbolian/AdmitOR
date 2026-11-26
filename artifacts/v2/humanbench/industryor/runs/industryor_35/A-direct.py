import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    task_times = params["task_times"]

    workers = list(range(5))
    tasks = list(range(4))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(workers, tasks, domain=pyo.Binary)
    model.y = pyo.Var(workers, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(task_times[i][j] * model.x[i, j] for i in workers for j in tasks),
        sense=pyo.minimize,
    )

    model.assign_task = pyo.ConstraintList()
    for j in tasks:
        model.assign_task.add(sum(model.x[i, j] for i in workers) == 1)

    model.one_worker_per_task = pyo.ConstraintList()
    for i in workers:
        model.one_worker_per_task.add(sum(model.x[i, j] for j in tasks) == model.y[i])

    model.exactly_four = pyo.Constraint(expr=sum(model.y[i] for i in workers) == 4)

    model.link = pyo.ConstraintList()
    for i in workers:
        for j in tasks:
            model.link.add(model.x[i, j] <= model.y[i])

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}