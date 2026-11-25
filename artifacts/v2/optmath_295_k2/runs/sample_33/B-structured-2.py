# IR: {"sets":{"E":"0..5","P":"0..6"},"params":{"employee_availability":"nonnegative[E]","project_requirement":"nonnegative[P]","assignment_cost":"real[E,P], nested rows or flat employee-major input","assignment_limit":"nonnegative[E,P], nested rows or flat employee-major input"},"variables":{"hours[E,P]":"continuous nonnegative"},"constraints":["sum(hours[e,p] for p in P) <= employee_availability[e] for e in E","sum(hours[e,p] for e in E) >= project_requirement[p] for p in P","hours[e,p] <= assignment_limit[e,p] for e in E, p in P"],"objective":"minimize sum(assignment_cost[e,p]*hours[e,p] for e in E, p in P)"}

from collections.abc import Sequence

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    employee_availability = params["employee_availability"]
    project_requirement = params["project_requirement"]
    assignment_cost = params["assignment_cost"]
    assignment_limit = params["assignment_limit"]

    def pair_value(values, employee, project):
        if isinstance(values[0], Sequence):
            return values[employee][project]
        return values[7 * employee + project]

    model = pyo.ConcreteModel()
    model.employees = pyo.RangeSet(0, 5)
    model.projects = pyo.RangeSet(0, 6)

    model.employee_availability = pyo.Param(
        model.employees,
        initialize=lambda mdl, employee: employee_availability[employee],
        within=pyo.NonNegativeReals,
    )
    model.project_requirement = pyo.Param(
        model.projects,
        initialize=lambda mdl, project: project_requirement[project],
        within=pyo.NonNegativeReals,
    )
    model.assignment_cost = pyo.Param(
        model.employees,
        model.projects,
        initialize=lambda mdl, employee, project: pair_value(
            assignment_cost, employee, project
        ),
        within=pyo.Reals,
    )
    model.assignment_limit = pyo.Param(
        model.employees,
        model.projects,
        initialize=lambda mdl, employee, project: pair_value(
            assignment_limit, employee, project
        ),
        within=pyo.NonNegativeReals,
    )

    model.hours = pyo.Var(
        model.employees,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    def employee_capacity_rule(mdl, employee):
        return (
            sum(mdl.hours[employee, project] for project in mdl.projects)
            <= mdl.employee_availability[employee]
        )

    model.employee_capacity = pyo.Constraint(
        model.employees,
        rule=employee_capacity_rule,
    )

    def project_demand_rule(mdl, project):
        return (
            sum(mdl.hours[employee, project] for employee in mdl.employees)
            >= mdl.project_requirement[project]
        )

    model.project_demand = pyo.Constraint(
        model.projects,
        rule=project_demand_rule,
    )

    def assignment_cap_rule(mdl, employee, project):
        return (
            mdl.hours[employee, project]
            <= mdl.assignment_limit[employee, project]
        )

    model.assignment_caps = pyo.Constraint(
        model.employees,
        model.projects,
        rule=assignment_cap_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[employee, project]
            * model.hours[employee, project]
            for employee in model.employees
            for project in model.projects
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}