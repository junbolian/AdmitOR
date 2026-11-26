# IR: {"sets":{"activities":["A","B","C","D","E","F","G"],"precedence":[["A","G"],["A","D"],["E","F"],["G","F"],["D","C"],["F","C"],["F","B"]]},"params":{"durations":"activity durations; mapping keyed by activity or sequence in A-G order","work_cost_per_day":"project cost per elapsed day","machine_cost_per_day":"rental cost per day from start of A through completion of B"},"variables":{"start[a]":"nonnegative continuous","completion":"nonnegative continuous"},"constraints":["start[j] >= start[i] + durations[i] for each precedence arc (i,j)","completion >= start[a] + durations[a] for each activity a"],"objective":"minimize work_cost_per_day * completion + machine_cost_per_day * (start[B] + durations[B] - start[A])"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    activities = ("A", "B", "C", "D", "E", "F", "G")
    precedence = (
        ("A", "G"),
        ("A", "D"),
        ("E", "F"),
        ("G", "F"),
        ("D", "C"),
        ("F", "C"),
        ("F", "B"),
    )

    supplied_durations = params["durations"]
    if isinstance(supplied_durations, Mapping):
        durations = {
            activity: supplied_durations[activity]
            for activity in activities
        }
    else:
        durations = {
            activity: supplied_durations[position]
            for position, activity in enumerate(activities)
        }

    work_cost_per_day = params["work_cost_per_day"]
    machine_cost_per_day = params["machine_cost_per_day"]

    model = pyo.ConcreteModel()
    model.activities = pyo.Set(initialize=activities, ordered=True)
    model.precedence_arcs = pyo.Set(
        initialize=precedence, dimen=2, ordered=True
    )

    model.duration = pyo.Param(
        model.activities,
        initialize=durations,
        within=pyo.NonNegativeReals,
    )
    model.work_rate = pyo.Param(
        initialize=work_cost_per_day,
        within=pyo.NonNegativeReals,
    )
    model.machine_rate = pyo.Param(
        initialize=machine_cost_per_day,
        within=pyo.NonNegativeReals,
    )

    model.start = pyo.Var(model.activities, domain=pyo.NonNegativeReals)
    model.completion = pyo.Var(domain=pyo.NonNegativeReals)

    def precedence_rule(project, predecessor, successor):
        return (
            project.start[successor]
            >= project.start[predecessor] + project.duration[predecessor]
        )

    model.precedence_constraints = pyo.Constraint(
        model.precedence_arcs, rule=precedence_rule
    )

    def completion_rule(project, activity):
        return (
            project.completion
            >= project.start[activity] + project.duration[activity]
        )

    model.completion_constraints = pyo.Constraint(
        model.activities, rule=completion_rule
    )

    # Daily work cost applies throughout the elapsed project duration.
    model.total_cost = pyo.Objective(
        expr=(
            model.work_rate * model.completion
            + model.machine_rate
            * (
                model.start["B"]
                + model.duration["B"]
                - model.start["A"]
            )
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