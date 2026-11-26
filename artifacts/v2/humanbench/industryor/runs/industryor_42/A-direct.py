import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cpu_freq = params["cpu_frequencies_ghz"]
    task_instr = params["task_instructions_bi"]
    n_tasks = int(params["num_tasks"])
    n_cpus = int(params["num_cpus"])

    tasks = range(n_tasks)
    cpus = range(n_cpus)

    # Execution time of task i on cpu j: instructions / frequency
    exec_time = {(i, j): task_instr[i] / cpu_freq[j] for i in tasks for j in cpus}

    model = pyo.ConcreteModel()

    # Assignment of task i to cpu j (binary)
    model.x = pyo.Var(tasks, cpus, domain=pyo.Binary)

    # Makespan (completion time of last task)
    model.makespan = pyo.Var(domain=pyo.NonNegativeReals)

    # Each task assigned to exactly one CPU
    model.assign_c = pyo.ConstraintList()
    for i in tasks:
        model.assign_c.add(sum(model.x[i, j] for j in cpus) == 1)

    # Makespan bounds the load on every CPU
    model.load_c = pyo.ConstraintList()
    for j in cpus:
        model.load_c.add(
            sum(exec_time[i, j] * model.x[i, j] for i in tasks) <= model.makespan
        )

    model.obj = pyo.Objective(expr=model.makespan, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}