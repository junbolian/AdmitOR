# IR: {"sets":{"P":"0..5","J":"0..7"},"params":{"member_time":"P -> number","project_effort":"J -> number","assignment_cost":"P x J -> number","per_pair_capacity":"P x J -> number"},"variables":{"x[p,j]":"continuous, nonnegative"},"constraints":["sum(j in J, x[p,j]) = member_time[p] for p in P","sum(p in P, x[p,j]) = project_effort[j] for j in J","x[p,j] <= per_pair_capacity[p,j] for (p,j) in P x J"],"objective":"minimize sum(p in P, j in J, assignment_cost[p,j] * x[p,j])"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept indexed vectors and nested matrices or tuple-keyed matrices."""
    member_time = params["member_time"]
    project_effort = params["project_effort"]
    assignment_cost = params["assignment_cost"]
    per_pair_capacity = params["per_pair_capacity"]

    def pair_value(data, person, project):
        if isinstance(data, Mapping) and (person, project) in data:
            return data[(person, project)]
        return data[person][project]

    model = pyo.ConcreteModel()
    model.people = pyo.Set(initialize=range(6), ordered=True)
    model.projects = pyo.Set(initialize=range(8), ordered=True)

    model.available_time = pyo.Param(
        model.people,
        initialize=lambda mdl, person: member_time[person],
    )
    model.required_effort = pyo.Param(
        model.projects,
        initialize=lambda mdl, project: project_effort[project],
    )
    model.unit_cost = pyo.Param(
        model.people,
        model.projects,
        initialize=lambda mdl, person, project: pair_value(
            assignment_cost, person, project
        ),
    )
    model.pair_capacity = pyo.Param(
        model.people,
        model.projects,
        initialize=lambda mdl, person, project: pair_value(
            per_pair_capacity, person, project
        ),
    )

    model.x = pyo.Var(
        model.people,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    model.person_balance = pyo.Constraint(
        model.people,
        rule=lambda mdl, person: sum(
            mdl.x[person, project] for project in mdl.projects
        ) == mdl.available_time[person],
    )

    model.project_balance = pyo.Constraint(
        model.projects,
        rule=lambda mdl, project: sum(
            mdl.x[person, project] for person in mdl.people
        ) == mdl.required_effort[project],
    )

    model.assignment_limits = pyo.Constraint(
        model.people,
        model.projects,
        rule=lambda mdl, person, project: (
            mdl.x[person, project] <= mdl.pair_capacity[person, project]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[person, project] * model.x[person, project]
            for person in model.people
            for project in model.projects
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}