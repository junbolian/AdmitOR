# IR: {"sets":{"T":"range(num_tasks)","C":"range(num_cpus)"},"params":{"num_tasks":"params['num_tasks']","num_cpus":"params['num_cpus']","cpu_frequencies_ghz":"params['cpu_frequencies_ghz'][c] > 0","task_instructions_bi":"params['task_instructions_bi'][t] >= 0"},"variables":{"assignment[t,c]":"Binary","makespan":"NonNegativeReals"},"constraints":["For each t: sum(c in C, assignment[t,c]) = 1","For each c: sum(t in T, task_instructions_bi[t]/cpu_frequencies_ghz[c]*assignment[t,c]) <= makespan"],"objective":"minimize makespan"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # The prose mentions 10 tasks, but supplies only seven instruction counts.
    # Use the supplied num_tasks and require one instruction count per task.
    # Tasks assigned to each CPU can execute sequentially in any order.
    frequencies = params["cpu_frequencies_ghz"]
    instructions = params["task_instructions_bi"]
    num_tasks = params["num_tasks"]
    num_cpus = params["num_cpus"]

    if num_tasks <= 0 or num_cpus <= 0:
        return {"objective": None, "status": "invalid_set_sizes"}

    if len(instructions) != num_tasks or len(frequencies) != num_cpus:
        return {"objective": None, "status": "invalid_dimensions"}

    if any(frequency <= 0 for frequency in frequencies):
        return {"objective": None, "status": "invalid_frequency"}

    if any(instruction_count < 0 for instruction_count in instructions):
        return {"objective": None, "status": "invalid_instructions"}

    model = pyo.ConcreteModel()

    model.task_ids = pyo.Set(initialize=range(num_tasks), ordered=True)
    model.cpu_ids = pyo.Set(initialize=range(num_cpus), ordered=True)

    model.cpu_frequency = pyo.Param(
        model.cpu_ids,
        initialize={cpu: frequencies[cpu] for cpu in range(num_cpus)},
        within=pyo.PositiveReals,
    )
    model.task_instructions = pyo.Param(
        model.task_ids,
        initialize={task: instructions[task] for task in range(num_tasks)},
        within=pyo.NonNegativeReals,
    )

    model.assignment = pyo.Var(
        model.task_ids, model.cpu_ids, domain=pyo.Binary
    )
    model.makespan = pyo.Var(domain=pyo.NonNegativeReals)

    def assign_once_rule(instance, task):
        return sum(
            instance.assignment[task, cpu] for cpu in instance.cpu_ids
        ) == 1

    model.assign_once = pyo.Constraint(
        model.task_ids, rule=assign_once_rule
    )

    def cpu_load_rule(instance, cpu):
        return sum(
            instance.task_instructions[task]
            / instance.cpu_frequency[cpu]
            * instance.assignment[task, cpu]
            for task in instance.task_ids
        ) <= instance.makespan

    model.cpu_load_limit = pyo.Constraint(
        model.cpu_ids, rule=cpu_load_rule
    )

    model.completion_objective = pyo.Objective(
        expr=model.makespan, sense=pyo.minimize
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.completion_objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}