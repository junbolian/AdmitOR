# IR: {"sets":{"persons":"0..5","projects":"0..7"},"params":{"member_capacity":"input[person]","project_requirement":"input[project]","assignment_cost":"input[person][project]; omitted from supplied data","assignment_capacity":"input[person][project]; omitted from supplied data"},"decision_variables":{"effort[person,project]":"NonNegativeReals"},"constraints":["sum_project effort[person,project] == member_capacity[person] for each person","sum_person effort[person,project] == project_requirement[project] for each project","effort[person,project] <= assignment_capacity[person][project] for each person,project"],"objective":"minimize sum_person,project assignment_cost[person][project]*effort[person,project]"}
#
# The supplied statement does not contain the complete cost or assignment
# capacity matrices. The two listed parameters alone cannot determine this
# optimization problem or its objective value. The example entries do not
# determine the missing entries, and inventing them would change the problem.
# This script solves the stated model when those matrices are also supplied;
# otherwise, it explicitly reports insufficient problem data.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    required_parameters = (
        "member_capacity",
        "project_requirement",
        "assignment_cost",
        "assignment_capacity",
    )
    if any(parameter not in params for parameter in required_parameters):
        return {"objective": None, "status": "insufficient_problem_data"}

    member_capacity = params["member_capacity"]
    project_requirement = params["project_requirement"]
    assignment_cost = params["assignment_cost"]
    assignment_capacity = params["assignment_capacity"]

    model = pyo.ConcreteModel()
    model.persons = pyo.RangeSet(0, 5)
    model.projects = pyo.RangeSet(0, 7)

    model.member_capacity = pyo.Param(
        model.persons,
        initialize=lambda instance, person: member_capacity[person],
        within=pyo.NonNegativeReals,
    )
    model.project_requirement = pyo.Param(
        model.projects,
        initialize=lambda instance, project: project_requirement[project],
        within=pyo.NonNegativeReals,
    )
    model.assignment_cost = pyo.Param(
        model.persons,
        model.projects,
        initialize=lambda instance, person, project: (
            assignment_cost[person][project]
        ),
        within=pyo.Reals,
    )
    model.assignment_capacity = pyo.Param(
        model.persons,
        model.projects,
        initialize=lambda instance, person, project: (
            assignment_capacity[person][project]
        ),
        within=pyo.NonNegativeReals,
    )

    model.effort = pyo.Var(
        model.persons,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    def member_balance_rule(instance, person):
        return (
            sum(
                instance.effort[person, project]
                for project in instance.projects
            )
            == instance.member_capacity[person]
        )

    def project_balance_rule(instance, project):
        return (
            sum(
                instance.effort[person, project]
                for person in instance.persons
            )
            == instance.project_requirement[project]
        )

    def assignment_limit_rule(instance, person, project):
        return (
            instance.effort[person, project]
            <= instance.assignment_capacity[person, project]
        )

    model.member_balance = pyo.Constraint(
        model.persons, rule=member_balance_rule
    )
    model.project_balance = pyo.Constraint(
        model.projects, rule=project_balance_rule
    )
    model.assignment_limit = pyo.Constraint(
        model.persons, model.projects, rule=assignment_limit_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[person, project]
            * model.effort[person, project]
            for person in model.persons
            for project in model.projects
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}