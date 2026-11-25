# IR: {"sets":{"employees":[0,1,2,3,4,5],"projects":[0,1,2,3,4]},"params":{"employee_hours":"nonnegative[employees]","project_hours":"nonnegative[projects]","cost":"real[employees,projects]","capacity":"nonnegative[employees,projects]"},"variables":{"hours":"continuous nonnegative[employees,projects]"},"constraints":["For each employee i: sum_j hours[i,j] = employee_hours[i]","For each project j: sum_i hours[i,j] = project_hours[j]","For each employee i and project j: hours[i,j] <= capacity[i,j]"],"objective":"minimize sum_i sum_j cost[i,j] * hours[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.employees = pyo.RangeSet(0, 5)
    model.projects = pyo.RangeSet(0, 4)

    model.employee_hours = pyo.Param(
        model.employees,
        initialize={
            employee: params["employee_hours"][employee]
            for employee in model.employees
        },
        within=pyo.NonNegativeReals,
    )

    model.project_hours = pyo.Param(
        model.projects,
        initialize={
            project: params["project_hours"][project]
            for project in model.projects
        },
        within=pyo.NonNegativeReals,
    )

    model.cost = pyo.Param(
        model.employees,
        model.projects,
        initialize={
            (employee, project): params["cost"][employee][project]
            for employee in model.employees
            for project in model.projects
        },
        within=pyo.Reals,
    )

    model.capacity = pyo.Param(
        model.employees,
        model.projects,
        initialize={
            (employee, project): params["capacity"][employee][project]
            for employee in model.employees
            for project in model.projects
        },
        within=pyo.NonNegativeReals,
    )

    model.hours = pyo.Var(
        model.employees,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    def employee_total_rule(problem, employee):
        return (
            sum(problem.hours[employee, project] for project in problem.projects)
            == problem.employee_hours[employee]
        )

    model.employee_totals = pyo.Constraint(
        model.employees,
        rule=employee_total_rule,
    )

    def project_total_rule(problem, project):
        return (
            sum(problem.hours[employee, project] for employee in problem.employees)
            == problem.project_hours[project]
        )

    model.project_totals = pyo.Constraint(
        model.projects,
        rule=project_total_rule,
    )

    def assignment_limit_rule(problem, employee, project):
        return (
            problem.hours[employee, project]
            <= problem.capacity[employee, project]
        )

    model.assignment_limits = pyo.Constraint(
        model.employees,
        model.projects,
        rule=assignment_limit_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[employee, project] * model.hours[employee, project]
            for employee in model.employees
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