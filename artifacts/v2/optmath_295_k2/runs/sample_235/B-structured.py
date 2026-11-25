# IR: {"sets":{"employees":"0..5","projects":"0..5"},"params":{"employee_availability":"employee-indexed hours","project_requirement":"project-indexed hours","assignment_cost":"employee-by-project costs","assignment_capacity":"employee-by-project maximum hours"},"variables":{"hours[i,j]":"nonnegative continuous"},"constraints":["sum_j hours[i,j] = employee_availability[i] for each employee i","sum_i hours[i,j] = project_requirement[j] for each project j","hours[i,j] <= assignment_capacity[i][j] for each employee-project pair"],"objective":"minimize sum_i sum_j assignment_cost[i][j] * hours[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    employee_availability = params["employee_availability"]
    project_requirement = params["project_requirement"]
    assignment_cost = params["assignment_cost"]
    assignment_capacity = params["assignment_capacity"]

    model = pyo.ConcreteModel()

    model.employees = pyo.RangeSet(0, 5)
    model.projects = pyo.RangeSet(0, 5)

    model.availability = pyo.Param(
        model.employees,
        initialize=lambda mdl, i: employee_availability[i],
        within=pyo.Reals,
    )
    model.requirement = pyo.Param(
        model.projects,
        initialize=lambda mdl, j: project_requirement[j],
        within=pyo.Reals,
    )
    model.unit_cost = pyo.Param(
        model.employees,
        model.projects,
        initialize=lambda mdl, i, j: assignment_cost[i][j],
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.employees,
        model.projects,
        initialize=lambda mdl, i, j: assignment_capacity[i][j],
        within=pyo.Reals,
    )

    model.hours = pyo.Var(
        model.employees,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    def employee_hours_rule(mdl, i):
        return (
            sum(mdl.hours[i, j] for j in mdl.projects)
            == mdl.availability[i]
        )

    model.employee_hours = pyo.Constraint(
        model.employees,
        rule=employee_hours_rule,
    )

    def project_hours_rule(mdl, j):
        return (
            sum(mdl.hours[i, j] for i in mdl.employees)
            == mdl.requirement[j]
        )

    model.project_hours = pyo.Constraint(
        model.projects,
        rule=project_hours_rule,
    )

    def assignment_limit_rule(mdl, i, j):
        return mdl.hours[i, j] <= mdl.capacity[i, j]

    model.assignment_limits = pyo.Constraint(
        model.employees,
        model.projects,
        rule=assignment_limit_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[i, j] * model.hours[i, j]
            for i in model.employees
            for j in model.projects
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