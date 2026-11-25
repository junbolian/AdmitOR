# IR: {"sets":{"persons":"0..6","projects":"0..6"},"params":{"availability":"persons -> hours","project_requirement":"projects -> hours","assignment_cost":"persons x projects -> cost/hour","per_project_limit":"persons x projects -> hours"},"variables":{"hours[person,project]":"continuous, nonnegative"},"constraints":["For each person: sum_project hours[person,project] <= availability[person]","For each project: sum_person hours[person,project] >= project_requirement[project]","For each person,project: hours[person,project] <= per_project_limit[person,project]"],"objective":"Minimize sum_person,project assignment_cost[person,project] * hours[person,project]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    availability = params["availability"]
    project_requirement = params["project_requirement"]
    assignment_cost = params["assignment_cost"]
    per_project_limit = params["per_project_limit"]

    model = pyo.ConcreteModel()
    model.persons = pyo.RangeSet(0, 6)
    model.projects = pyo.RangeSet(0, 6)

    model.availability = pyo.Param(
        model.persons,
        initialize={person: availability[person] for person in model.persons},
    )
    model.project_requirement = pyo.Param(
        model.projects,
        initialize={
            project: project_requirement[project] for project in model.projects
        },
    )
    model.assignment_cost = pyo.Param(
        model.persons,
        model.projects,
        initialize={
            (person, project): assignment_cost[person][project]
            for person in model.persons
            for project in model.projects
        },
    )
    model.per_project_limit = pyo.Param(
        model.persons,
        model.projects,
        initialize={
            (person, project): per_project_limit[person][project]
            for person in model.persons
            for project in model.projects
        },
    )

    model.hours = pyo.Var(
        model.persons, model.projects, domain=pyo.NonNegativeReals
    )

    def availability_rule(model, person):
        return (
            sum(model.hours[person, project] for project in model.projects)
            <= model.availability[person]
        )

    model.availability_constraints = pyo.Constraint(
        model.persons, rule=availability_rule
    )

    def requirement_rule(model, project):
        return (
            sum(model.hours[person, project] for person in model.persons)
            >= model.project_requirement[project]
        )

    model.requirement_constraints = pyo.Constraint(
        model.projects, rule=requirement_rule
    )

    def assignment_limit_rule(model, person, project):
        return (
            model.hours[person, project]
            <= model.per_project_limit[person, project]
        )

    model.assignment_limit_constraints = pyo.Constraint(
        model.persons, model.projects, rule=assignment_limit_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[person, project] * model.hours[person, project]
            for person in model.persons
            for project in model.projects
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