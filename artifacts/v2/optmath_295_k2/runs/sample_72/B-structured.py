# IR: {"sets":{"employees":[0,1,2,3,4],"projects":[0,1,2,3,4]},"params":{"assignment_cost":"real[employees,projects]","employee_total_capacity":"nonnegative_real[employees]","employee_project_limit":"nonnegative_real[employees,projects]","project_demand":"nonnegative_real[projects]"},"variables":{"assigned_units":"nonnegative_real[employees,projects]"},"constraints":["For each employee: sum_project assigned_units[employee,project] = employee_total_capacity[employee]","For each project: sum_employee assigned_units[employee,project] = project_demand[project]","For each employee,project: assigned_units[employee,project] <= employee_project_limit[employee,project]"],"objective":"minimize sum_employee,project assignment_cost[employee,project] * assigned_units[employee,project]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    assignment_cost = params["assignment_cost"]
    employee_total_capacity = params["employee_total_capacity"]
    employee_project_limit = params["employee_project_limit"]
    project_demand = params["project_demand"]

    model = pyo.ConcreteModel()

    model.employees = pyo.RangeSet(0, 4)
    model.projects = pyo.RangeSet(0, 4)

    model.assignment_cost = pyo.Param(
        model.employees,
        model.projects,
        initialize=lambda _, employee, project: assignment_cost[employee][project],
        within=pyo.Reals,
    )
    model.employee_total_capacity = pyo.Param(
        model.employees,
        initialize=lambda _, employee: employee_total_capacity[employee],
        within=pyo.NonNegativeReals,
    )
    model.employee_project_limit = pyo.Param(
        model.employees,
        model.projects,
        initialize=lambda _, employee, project: employee_project_limit[employee][project],
        within=pyo.NonNegativeReals,
    )
    model.project_demand = pyo.Param(
        model.projects,
        initialize=lambda _, project: project_demand[project],
        within=pyo.NonNegativeReals,
    )

    model.assigned_units = pyo.Var(
        model.employees,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    def employee_total_rule(instance, employee):
        return (
            sum(
                instance.assigned_units[employee, project]
                for project in instance.projects
            )
            == instance.employee_total_capacity[employee]
        )

    model.employee_total_constraint = pyo.Constraint(
        model.employees,
        rule=employee_total_rule,
    )

    def project_total_rule(instance, project):
        return (
            sum(
                instance.assigned_units[employee, project]
                for employee in instance.employees
            )
            == instance.project_demand[project]
        )

    model.project_total_constraint = pyo.Constraint(
        model.projects,
        rule=project_total_rule,
    )

    def pair_limit_rule(instance, employee, project):
        return (
            instance.assigned_units[employee, project]
            <= instance.employee_project_limit[employee, project]
        )

    model.pair_limit_constraint = pyo.Constraint(
        model.employees,
        model.projects,
        rule=pair_limit_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[employee, project]
            * model.assigned_units[employee, project]
            for employee in model.employees
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
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}