# IR: {"sets":{"people":"0..5","projects":"0..7"},"params":{"member_time":"people -> nonnegative real","project_effort":"projects -> nonnegative real","assignment_cost":"people x projects -> real","per_pair_capacity":"people x projects -> nonnegative real"},"variables":{"assigned":"people x projects -> nonnegative continuous"},"constraints":["For each person: sum_project assigned[person,project] = member_time[person]","For each project: sum_person assigned[person,project] = project_effort[project]","For each pair: assigned[person,project] <= per_pair_capacity[person,project]"],"objective":"minimize sum_person,project assignment_cost[person,project] * assigned[person,project]"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _pair_value(data, person, project):
    """Accept tuple-keyed mappings or nested sequences/mappings."""
    if isinstance(data, Mapping) and (person, project) in data:
        return data[person, project]
    return data[person][project]


def solve(params):
    model = pyo.ConcreteModel()

    model.people = pyo.RangeSet(0, 5)
    model.projects = pyo.RangeSet(0, 7)

    model.member_time = pyo.Param(
        model.people,
        initialize=lambda mdl, person: params["member_time"][person],
        within=pyo.NonNegativeReals,
    )
    model.project_effort = pyo.Param(
        model.projects,
        initialize=lambda mdl, project: params["project_effort"][project],
        within=pyo.NonNegativeReals,
    )
    model.assignment_cost = pyo.Param(
        model.people,
        model.projects,
        initialize=lambda mdl, person, project: _pair_value(
            params["assignment_cost"], person, project
        ),
        within=pyo.Reals,
    )
    model.per_pair_capacity = pyo.Param(
        model.people,
        model.projects,
        initialize=lambda mdl, person, project: _pair_value(
            params["per_pair_capacity"], person, project
        ),
        within=pyo.NonNegativeReals,
    )

    model.assigned = pyo.Var(
        model.people,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    model.member_balance = pyo.Constraint(
        model.people,
        rule=lambda mdl, person: sum(
            mdl.assigned[person, project] for project in mdl.projects
        ) == mdl.member_time[person],
    )
    model.project_balance = pyo.Constraint(
        model.projects,
        rule=lambda mdl, project: sum(
            mdl.assigned[person, project] for person in mdl.people
        ) == mdl.project_effort[project],
    )
    model.pair_capacity_limit = pyo.Constraint(
        model.people,
        model.projects,
        rule=lambda mdl, person, project: (
            mdl.assigned[person, project]
            <= mdl.per_pair_capacity[person, project]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[person, project]
            * model.assigned[person, project]
            for person in model.people
            for project in model.projects
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}