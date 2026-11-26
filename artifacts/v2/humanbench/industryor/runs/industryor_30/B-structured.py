# IR = {
#   "sets": {"activities": ["A","B","C","D","E","F","G"], "precedence": [["A","G"],["A","D"],["E","F"],["G","F"],["D","C"],["F","C"],["F","B"]]},
#   "params": {"duration_A": "nonnegative days", "duration_B": "nonnegative days", "duration_C": "nonnegative days", "duration_D": "nonnegative days", "duration_E": "nonnegative days", "duration_F": "nonnegative days", "duration_G": "nonnegative days", "daily_work_cost": "nonnegative euros/day", "daily_machinery_cost": "nonnegative euros/day"},
#   "variables": {"start[a]": "continuous nonnegative, a in activities", "project_end": "continuous nonnegative"},
#   "constraints": [
#     "start[j] >= start[i] + duration[i] for (i,j) in precedence",
#     "project_end >= start[a] + duration[a] for a in activities"
#   ],
#   "objective": "minimize daily_work_cost * project_end + daily_machinery_cost * (start[B] + duration[B] - start[A])"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    durations = {
        "A": params["duration_A"],
        "B": params["duration_B"],
        "C": params["duration_C"],
        "D": params["duration_D"],
        "E": params["duration_E"],
        "F": params["duration_F"],
        "G": params["duration_G"],
    }

    model = pyo.ConcreteModel()

    model.activities = pyo.Set(
        initialize=["A", "B", "C", "D", "E", "F", "G"],
        ordered=True,
    )
    model.precedence = pyo.Set(
        dimen=2,
        initialize=[
            ("A", "G"),
            ("A", "D"),
            ("E", "F"),
            ("G", "F"),
            ("D", "C"),
            ("F", "C"),
            ("F", "B"),
        ],
    )

    model.duration = pyo.Param(
        model.activities,
        initialize=durations,
        within=pyo.NonNegativeReals,
    )
    model.daily_work_cost = pyo.Param(
        initialize=params["daily_work_cost"],
        within=pyo.NonNegativeReals,
    )
    model.daily_machinery_cost = pyo.Param(
        initialize=params["daily_machinery_cost"],
        within=pyo.NonNegativeReals,
    )

    model.start = pyo.Var(model.activities, domain=pyo.NonNegativeReals)
    model.project_end = pyo.Var(domain=pyo.NonNegativeReals)

    def precedence_rule(instance, predecessor, successor):
        return (
            instance.start[successor]
            >= instance.start[predecessor] + instance.duration[predecessor]
        )

    model.precedence_constraints = pyo.Constraint(
        model.precedence,
        rule=precedence_rule,
    )

    def completion_rule(instance, activity):
        return (
            instance.project_end
            >= instance.start[activity] + instance.duration[activity]
        )

    model.completion_constraints = pyo.Constraint(
        model.activities,
        rule=completion_rule,
    )

    # Ordinary work is charged over the project horizon; machinery is
    # rented continuously from A's start through B's completion.
    model.total_cost = pyo.Objective(
        expr=(
            model.daily_work_cost * model.project_end
            + model.daily_machinery_cost
            * (model.start["B"] + model.duration["B"] - model.start["A"])
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}