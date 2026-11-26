# IR: {"sets":{"tasks":[1,2,3],"modes":["t1_skilled","t1_team","t2_skilled","t2_laborer","t3_laborers","t3_team"]},"params":["wage_skilled","wage_laborer","eff_hours_skilled","eff_hours_laborer","demand_task1","demand_task2","demand_task3","max_skilled","max_laborers"],"structural_data":{"task_by_mode":[1,1,2,2,3,3],"skilled_per_mode":[1,1,1,0,0,1],"laborers_per_mode":[0,2,0,1,5,3]},"assumptions":["Assignments count whole-week individuals or complete teams assigned exclusively to one task.","Team output is the sum of its members' effective worker-hours."],"variables":{"recruited_skilled":"NonNegativeIntegers","recruited_laborers":"NonNegativeIntegers","assigned[mode]":"NonNegativeIntegers"},"constraints":["sum(skilled_per_mode[mode]*assigned[mode]) <= recruited_skilled","sum(laborers_per_mode[mode]*assigned[mode]) <= recruited_laborers","recruited_skilled <= max_skilled","recruited_laborers <= max_laborers","For each task: sum((skilled_per_mode[mode]*eff_hours_skilled + laborers_per_mode[mode]*eff_hours_laborer)*assigned[mode] for its modes) >= demand[task]"],"objective":"minimize wage_skilled*recruited_skilled + wage_laborer*recruited_laborers"}
#
# Feasibility note:
# Under the additive effective-worker-hour interpretation above, total demand
# cannot exceed max_skilled*eff_hours_skilled + max_laborers*eff_hours_laborer.
# The example data violate this necessary condition. A solver failure to load
# a feasible solution therefore does not, by itself, indicate a coding error.
# No additional productivity multiplier is specified in the problem.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    mode_data = {
        "t1_skilled": (1, 1, 0),
        "t1_team": (1, 1, 2),
        "t2_skilled": (2, 1, 0),
        "t2_laborer": (2, 0, 1),
        "t3_laborers": (3, 0, 5),
        "t3_team": (3, 1, 3),
    }

    model.tasks = pyo.Set(initialize=[1, 2, 3], ordered=True)
    model.modes = pyo.Set(initialize=list(mode_data), ordered=True)

    model.wage_skilled = pyo.Param(
        initialize=params["wage_skilled"], within=pyo.NonNegativeReals
    )
    model.wage_laborer = pyo.Param(
        initialize=params["wage_laborer"], within=pyo.NonNegativeReals
    )
    model.eff_hours_skilled = pyo.Param(
        initialize=params["eff_hours_skilled"], within=pyo.NonNegativeReals
    )
    model.eff_hours_laborer = pyo.Param(
        initialize=params["eff_hours_laborer"], within=pyo.NonNegativeReals
    )
    model.demand = pyo.Param(
        model.tasks,
        initialize={
            1: params["demand_task1"],
            2: params["demand_task2"],
            3: params["demand_task3"],
        },
        within=pyo.NonNegativeReals,
    )
    model.max_skilled = pyo.Param(
        initialize=params["max_skilled"], within=pyo.NonNegativeReals
    )
    model.max_laborers = pyo.Param(
        initialize=params["max_laborers"], within=pyo.NonNegativeReals
    )

    model.recruited_skilled = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.recruited_laborers = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.assigned = pyo.Var(model.modes, domain=pyo.NonNegativeIntegers)

    model.skilled_staffing = pyo.Constraint(
        expr=sum(
            mode_data[mode][1] * model.assigned[mode]
            for mode in model.modes
        )
        <= model.recruited_skilled
    )
    model.laborer_staffing = pyo.Constraint(
        expr=sum(
            mode_data[mode][2] * model.assigned[mode]
            for mode in model.modes
        )
        <= model.recruited_laborers
    )
    model.skilled_recruitment_limit = pyo.Constraint(
        expr=model.recruited_skilled <= model.max_skilled
    )
    model.laborer_recruitment_limit = pyo.Constraint(
        expr=model.recruited_laborers <= model.max_laborers
    )

    def task_requirement_rule(instance, task):
        return sum(
            (
                mode_data[mode][1] * instance.eff_hours_skilled
                + mode_data[mode][2] * instance.eff_hours_laborer
            )
            * instance.assigned[mode]
            for mode in instance.modes
            if mode_data[mode][0] == task
        ) >= instance.demand[task]

    model.task_requirements = pyo.Constraint(
        model.tasks, rule=task_requirement_rule
    )

    model.total_wages = pyo.Objective(
        expr=(
            model.wage_skilled * model.recruited_skilled
            + model.wage_laborer * model.recruited_laborers
        ),
        sense=pyo.minimize,
    )

    # Appsi HiGHS can raise RuntimeError when no solution can be loaded.
    # Regardless, determine success solely by objective retrievability.
    solve_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        solve_failed = True

    try:
        obj_val = float(pyo.value(model.total_wages))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": (
                "infeasible_or_failed"
                if solve_failed
                else "objective_unavailable"
            ),
        }

    return {"objective": obj_val, "status": "optimal"}