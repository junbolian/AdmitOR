# IR: {"sets":{"I":"0..6","J":"0..6"},"params":{"availability":"availability[i], nonnegative","demand":"demand[j], nonnegative","cost":"cost[i,j], real","pair_cap":"pair_cap[i,j], nonnegative"},"variables":{"hours[i,j]":"nonnegative continuous"},"constraints":["sum(j in J, hours[i,j]) <= availability[i] for i in I","sum(i in I, hours[i,j]) >= demand[j] for j in J","hours[i,j] <= pair_cap[i,j] for i in I, j in J"],"objective":"minimize sum(i in I, j in J, cost[i,j] * hours[i,j])"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept vectors and nested matrices, or matrices keyed by (i, j)."""
    availability = params["availability"]
    demand = params["demand"]
    cost = params["cost"]
    pair_cap = params["pair_cap"]

    def matrix_value(data, person, project):
        if isinstance(data, Mapping) and (person, project) in data:
            return data[person, project]
        return data[person][project]

    model = pyo.ConcreteModel()
    model.people = pyo.RangeSet(0, 6)
    model.projects = pyo.RangeSet(0, 6)

    model.available_hours = pyo.Param(
        model.people,
        initialize=lambda mdl, person: availability[person],
        within=pyo.NonNegativeReals,
    )
    model.required_hours = pyo.Param(
        model.projects,
        initialize=lambda mdl, project: demand[project],
        within=pyo.NonNegativeReals,
    )
    model.hourly_cost = pyo.Param(
        model.people,
        model.projects,
        initialize=lambda mdl, person, project: matrix_value(
            cost, person, project
        ),
        within=pyo.Reals,
    )
    model.assignment_cap = pyo.Param(
        model.people,
        model.projects,
        initialize=lambda mdl, person, project: matrix_value(
            pair_cap, person, project
        ),
        within=pyo.NonNegativeReals,
    )

    model.hours = pyo.Var(
        model.people,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    model.availability_limits = pyo.Constraint(
        model.people,
        rule=lambda mdl, person: (
            sum(mdl.hours[person, project] for project in mdl.projects)
            <= mdl.available_hours[person]
        ),
    )
    model.project_requirements = pyo.Constraint(
        model.projects,
        rule=lambda mdl, project: (
            sum(mdl.hours[person, project] for person in mdl.people)
            >= mdl.required_hours[project]
        ),
    )
    model.pair_limits = pyo.Constraint(
        model.people,
        model.projects,
        rule=lambda mdl, person, project: (
            mdl.hours[person, project] <= mdl.assignment_cap[person, project]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.hourly_cost[person, project] * model.hours[person, project]
            for person in model.people
            for project in model.projects
        ),
        sense=pyo.minimize,
    )

    solve_failure = None
    try:
        Highs().solve(model)
    except RuntimeError:
        solve_failure = "solve_failed"

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": solve_failure or "objective_unavailable",
        }

    return {"objective": obj_val, "status": "optimal"}