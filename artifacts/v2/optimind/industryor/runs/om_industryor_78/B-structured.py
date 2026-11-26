# IR: {"sets":{"tasks":[1,2,3],"modes":[[1,"skilled"],[1,"mixed"],[2,"skilled"],[2,"laborer"],[3,"laborers"],[3,"mixed"]]},"params":["wage_skilled","wage_laborer","effective_hours_skilled","effective_hours_laborer","demand_task1","demand_task2","demand_task3","max_skilled","max_laborers"],"structural_data":{"skilled_per_mode":[1,1,1,0,0,1],"laborers_per_mode":[0,2,0,1,5,3]},"variables":{"crew_count[mode]":"nonnegative integer","hired_skilled":"nonnegative integer","hired_laborers":"nonnegative integer"},"constraints":["hired_skilled = sum(skilled_per_mode[mode] * crew_count[mode])","hired_laborers = sum(laborers_per_mode[mode] * crew_count[mode])","hired_skilled <= max_skilled","hired_laborers <= max_laborers","For each task: sum((skilled_per_mode[mode] * effective_hours_skilled + laborers_per_mode[mode] * effective_hours_laborer) * crew_count[mode] for modes belonging to task) >= demand_task"],"objective":"minimize wage_skilled * hired_skilled + wage_laborer * hired_laborers"}
#
# Modeling interpretation: required effective working hours are aggregate
# person-hours. Workers are assigned to one task for the week, and mixed
# crews contribute the sum of their members' effective weekly hours.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    mode_keys = (
        (1, "skilled"),
        (1, "mixed"),
        (2, "skilled"),
        (2, "laborer"),
        (3, "laborers"),
        (3, "mixed"),
    )

    skilled_requirements = dict(zip(mode_keys, (1, 1, 1, 0, 0, 1)))
    laborer_requirements = dict(zip(mode_keys, (0, 2, 0, 1, 5, 3)))

    model.tasks = pyo.Set(initialize=(1, 2, 3), ordered=True)
    model.modes = pyo.Set(initialize=mode_keys, dimen=2, ordered=True)

    model.wage_skilled = pyo.Param(
        initialize=params["wage_skilled"]
    )
    model.wage_laborer = pyo.Param(
        initialize=params["wage_laborer"]
    )
    model.effective_hours_skilled = pyo.Param(
        initialize=params["effective_hours_skilled"]
    )
    model.effective_hours_laborer = pyo.Param(
        initialize=params["effective_hours_laborer"]
    )
    model.required_hours = pyo.Param(
        model.tasks,
        initialize={
            1: params["demand_task1"],
            2: params["demand_task2"],
            3: params["demand_task3"],
        },
    )
    model.max_skilled = pyo.Param(
        initialize=params["max_skilled"]
    )
    model.max_laborers = pyo.Param(
        initialize=params["max_laborers"]
    )

    model.skilled_per_mode = pyo.Param(
        model.modes, initialize=skilled_requirements
    )
    model.laborers_per_mode = pyo.Param(
        model.modes, initialize=laborer_requirements
    )

    model.crew_count = pyo.Var(
        model.modes, domain=pyo.NonNegativeIntegers
    )
    model.hired_skilled = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.hired_laborers = pyo.Var(domain=pyo.NonNegativeIntegers)

    model.skilled_assignment = pyo.Constraint(
        expr=model.hired_skilled
        == sum(
            model.skilled_per_mode[task, mode_name]
            * model.crew_count[task, mode_name]
            for task, mode_name in model.modes
        )
    )
    model.laborer_assignment = pyo.Constraint(
        expr=model.hired_laborers
        == sum(
            model.laborers_per_mode[task, mode_name]
            * model.crew_count[task, mode_name]
            for task, mode_name in model.modes
        )
    )
    model.skilled_recruitment_limit = pyo.Constraint(
        expr=model.hired_skilled <= model.max_skilled
    )
    model.laborer_recruitment_limit = pyo.Constraint(
        expr=model.hired_laborers <= model.max_laborers
    )

    def task_coverage_rule(instance, task):
        return sum(
            (
                instance.skilled_per_mode[task_id, mode_name]
                * instance.effective_hours_skilled
                + instance.laborers_per_mode[task_id, mode_name]
                * instance.effective_hours_laborer
            )
            * instance.crew_count[task_id, mode_name]
            for task_id, mode_name in instance.modes
            if task_id == task
        ) >= instance.required_hours[task]

    model.task_coverage = pyo.Constraint(
        model.tasks, rule=task_coverage_rule
    )

    model.total_wage = pyo.Objective(
        expr=(
            model.wage_skilled * model.hired_skilled
            + model.wage_laborer * model.hired_laborers
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_wage))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}